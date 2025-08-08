from flask import render_template, request, jsonify, url_for, current_app
from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

from crunevo.extensions import db
from crunevo.models import (
    Post,
    PostComment,
    PostReaction,
    FeedItem,
    Note,
    User,
)
from crunevo.utils.helpers import activated_required
from crunevo.utils import send_notification, record_activity
from crunevo.utils.credits import add_credit, spend_credit
from crunevo.constants import CreditReasons
from crunevo.cache.feed_cache import fetch as cache_fetch, push_items as cache_push
from sqlalchemy.exc import IntegrityError

from . import feed_bp


@feed_bp.route("/api/comments/<int:post_id>", methods=["GET"])
def api_comments(post_id):
    """Return paginated comments for a post."""
    post = Post.query.get_or_404(post_id)
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    query = PostComment.query.filter_by(post_id=post.id, pending=False).order_by(
        PostComment.timestamp.desc()
    )
    comments = query.offset((page - 1) * per_page).limit(per_page + 1).all()
    has_more = len(comments) > per_page
    comments = comments[:per_page]

    formatted = []
    for comment in comments:
        formatted.append(
            {
                "id": comment.id,
                "body": comment.body,
                "timestamp_text": (
                    (
                        comment.timestamp.strftime("%d/%m/%Y %H:%M")
                        if comment.timestamp
                        else ""
                    ),
                ),
                "author": {
                    "username": (
                        comment.author.username
                        if comment.author
                        else "Usuario eliminado"
                    ),
                    "avatar_url": (
                        comment.author.avatar_url
                        if comment.author
                        else url_for("static", filename="img/default.png")
                    ),
                },
            }
        )

    return jsonify({"post_id": post_id, "comments": formatted, "has_more": has_more})


@feed_bp.route("/like/<int:post_id>", methods=["POST"])
@activated_required
def like_post(post_id):
    """Handle reactions to a post allowing one per user."""
    post = Post.query.get_or_404(post_id)
    reaction = request.form.get("reaction", "🔥")
    existing = PostReaction.query.filter_by(
        user_id=current_user.id, post_id=post.id
    ).first()

    if existing:
        if existing.reaction_type == reaction:
            db.session.delete(existing)
            action = "removed"
        else:
            existing.reaction_type = reaction
            action = "changed"
    else:
        db.session.add(
            PostReaction(
                user_id=current_user.id,
                post_id=post.id,
                reaction_type=reaction,
            )
        )
        action = "added"
        if post.author_id != current_user.id:
            send_notification(
                post.author_id,
                f"{current_user.username} reaccionó a tu publicación",
                url_for("feed.view_post", post_id=post.id),
            )

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = PostReaction.query.filter_by(
            user_id=current_user.id, post_id=post.id
        ).first()
        if existing:
            if existing.reaction_type == reaction:
                action = "added"
            else:
                existing.reaction_type = reaction
                action = "changed"
            db.session.commit()

    counts = dict(
        db.session.query(PostReaction.reaction_type, db.func.count())
        .filter_by(post_id=post.id)
        .group_by(PostReaction.reaction_type)
        .all()
    )
    return jsonify({"counts": counts, "status": action})


@feed_bp.route("/comment/<int:post_id>", methods=["POST"])
@activated_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.comment_permission == "none" and post.author_id != current_user.id:
        current_app.logger.info(
            "Comment blocked: comments disabled user=%s post=%s",
            current_user.id,
            post_id,
        )
        return jsonify({"error": "Comentarios deshabilitados"}), 403
    if post.comment_permission == "friends" and post.author_id != current_user.id:
        if hasattr(post.author, "is_friend") and not post.author.is_friend(current_user):
            current_app.logger.info(
                "Comment blocked: friend-only user=%s post=%s",
                current_user.id,
                post_id,
            )
            return jsonify({"error": "Solo amigos pueden comentar"}), 403
    body = request.form.get("body", "").strip()
    if not body:
        current_app.logger.info(
            "Comment failed: empty body user=%s post=%s",
            current_user.id,
            post_id,
        )
        return jsonify({"error": "Comentario vacío"}), 400
    comment = PostComment(body=body, author=current_user, post=post)
    db.session.add(comment)
    db.session.commit()
    record_activity("comment_post", comment.id, "post")
    return jsonify(
        {
            "body": comment.body,
            "author": comment.author.username,
            "avatar": comment.author.avatar_url
            or url_for("static", filename="img/default.png"),
            "timestamp": comment.timestamp.strftime("%Y-%m-%d %H:%M"),
        }
    )


@feed_bp.route("/comment/delete/<int:comment_id>", methods=["POST"])
@activated_required
def delete_comment(comment_id: int):
    """Delete a comment if the requester is the author or a moderator/admin."""
    comment = PostComment.query.get_or_404(comment_id)
    if comment.author_id != current_user.id and current_user.role not in (
        "admin",
        "moderator",
    ):
        return jsonify({"error": "No autorizado"}), 403
    db.session.delete(comment)
    db.session.commit()
    return jsonify({"success": True})


@feed_bp.route("/api/post/<int:post_id>")
def api_post_detail(post_id: int):
    """Return rendered HTML for a post used in the comment modal."""
    post = Post.query.get_or_404(post_id)
    counts = PostReaction.count_for_post(post.id)
    my_reaction = (
        PostReaction.query.with_entities(PostReaction.reaction_type)
        .filter_by(user_id=current_user.id, post_id=post.id)
        .scalar()
    )
    from crunevo.models import SavedPost

    saved = (
        SavedPost.query.filter_by(user_id=current_user.id, post_id=post.id).first()
        is not None
    )
    comments = (
        PostComment.query.filter_by(post_id=post.id, pending=False)
        .order_by(PostComment.timestamp.desc())
        .limit(10)
        .all()
    )
    html = render_template(
        "feed/_post_modal.html",
        post=post,
        comments=comments,
        reaction_counts=counts,
        user_reaction=my_reaction,
        saved_posts={post.id: saved},
    )
    return jsonify({"html": html})


@feed_bp.route("/api/reactions/<int:post_id>")
@activated_required
def api_reactions(post_id: int):
    """Return users grouped by reaction type for a post."""
    Post.query.get_or_404(post_id)
    rows = (
        db.session.query(PostReaction.reaction_type, User.username, User.avatar_url)
        .join(User, PostReaction.user_id == User.id)
        .filter(PostReaction.post_id == post_id)
        .all()
    )
    result = {}
    for reaction, username, avatar in rows:
        result.setdefault(reaction, []).append(
            {
                "username": username,
                "avatar": avatar or url_for("static", filename="img/default.png"),
            }
        )
    return jsonify(result)


@feed_bp.route("/save/<int:post_id>", methods=["POST"])
@activated_required
def toggle_save(post_id):
    """Add or remove a post from the user's saved list."""
    post = Post.query.get_or_404(post_id)
    from crunevo.models import SavedPost

    saved = SavedPost.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if saved:
        db.session.delete(saved)
        db.session.commit()
        return jsonify({"saved": False})
    db.session.add(SavedPost(user_id=current_user.id, post_id=post.id))
    db.session.commit()
    return jsonify({"saved": True})


@feed_bp.route("/donate/<int:post_id>", methods=["POST"])
@activated_required
def donate_post(post_id):
    """Transfer credits to the author of a post."""
    post = Post.query.get_or_404(post_id)
    amount = request.form.get("amount", type=int, default=1)
    amount = max(1, min(5, amount))
    try:
        spend_credit(
            current_user, amount, CreditReasons.DONACION_FEED, related_id=post.id
        )
        add_credit(post.author, amount, CreditReasons.DONACION_FEED, related_id=post.id)
    except ValueError:
        return jsonify({"error": "Crolars insuficientes"}), 400
    return jsonify({"success": True})


@feed_bp.route("/api/chat", methods=["POST"])
@activated_required
def api_chat():
    question = request.json.get("question")
    return jsonify({"answer": f'Respuesta a "{question}"'})


@feed_bp.route("/api/analizar", methods=["POST"])
@activated_required
def api_analizar():
    text = request.json.get("text")
    return jsonify({"analysis": f"Analisis simple de {len(text)} caracteres"})


@feed_bp.route("/api/feed")
@activated_required
def api_feed():
    page = int(request.args.get("page", 1))
    categoria = request.args.get("categoria")
    fmt = request.args.get("format")
    start = (page - 1) * 10
    stop = start + 9
    items = [
        i
        for i in cache_fetch(current_user.id, start, stop)
        if i.get("item_type") != "apunte"
    ]
    if not items:
        q = (
            FeedItem.query.filter_by(owner_id=current_user.id)
            .filter(FeedItem.item_type != "apunte")
            .order_by(FeedItem.score.desc(), FeedItem.created_at.desc())
            .offset(start)
            .limit(10)
            .all()
        )
        items = [fi.to_dict() for fi in q]
        cache_push(
            current_user.id,
            [
                {"score": fi.score, "created_at": fi.created_at, "payload": item}
                for fi, item in zip(q, items)
            ],
        )

    seen = set()
    unique_items = []
    for it in items:
        if it.get("item_type") == "post":
            pid = it.get("ref_id")
            if pid in seen:
                continue
            seen.add(pid)
        unique_items.append(it)
    items = unique_items
    if categoria == "apuntes":
        items = [i for i in items if i.get("item_type") == "apunte"]
    elif categoria == "imagen":
        items = [
            i
            for i in items
            if i.get("item_type") == "post"
            and i.get("file_url")
            and not i.get("file_url", "").endswith(".pdf")
        ]

    post_ids = [i.get("ref_id") for i in items if i.get("item_type") == "post"]
    reaction_map = PostReaction.counts_for_posts(post_ids)
    user_reactions = PostReaction.reactions_for_user_posts(current_user.id, post_ids)
    from crunevo.models import SavedPost

    saved_posts = {
        sp.post_id: True
        for sp in SavedPost.query.filter(
            SavedPost.user_id == current_user.id,
            SavedPost.post_id.in_(post_ids),
        ).all()
    }

    if fmt == "html":
        if not post_ids:
            return jsonify({"html": "", "count": 0})
        posts = Post.query.filter(Post.id.in_(post_ids)).all()
        post_map = {p.id: p for p in posts}
        ordered_posts = [post_map[pid] for pid in post_ids if pid in post_map]
        html = render_template(
            "feed/_posts.html",
            posts=ordered_posts,
            reaction_counts=reaction_map,
            user_reactions=user_reactions,
            saved_posts=saved_posts,
        )
        return jsonify({"html": html, "count": len(ordered_posts)})

    for it in items:
        if it.get("item_type") == "post":
            pid = it.get("ref_id")
            it["reaction_counts"] = reaction_map.get(pid, {})
            it["user_reaction"] = user_reactions.get(pid)
            it["is_saved"] = pid in saved_posts

    return jsonify(items)


@feed_bp.route("/api/quickfeed")
@activated_required
def api_quickfeed():
    """Return feed items filtered for quick toggles."""
    filter_opt = request.args.get("filter", "recientes")
    if filter_opt == "apuntes":
        notes = Note.query.order_by(Note.created_at.desc()).limit(20).all()
        html = render_template("feed/_notes.html", notes=notes)
        return jsonify({"html": html, "count": len(notes)})

    query = Post.query
    if filter_opt == "populares":
        query = (
            query.join(PostReaction)
            .group_by(Post.id)
            .order_by(func.count(PostReaction.id).desc())
        )
    elif filter_opt == "relevantes":
        week_start = datetime.utcnow() - timedelta(days=7)
        query = (
            query.join(PostReaction)
            .filter(Post.created_at >= week_start)
            .group_by(Post.id)
            .order_by(func.count(PostReaction.id).desc())
        )
    else:
        query = query.order_by(Post.created_at.desc())

    posts = query.limit(20).all()
    html = render_template("feed/_posts.html", posts=posts)
    return jsonify({"html": html, "count": len(posts)})


@feed_bp.route("/api/trending")
@activated_required
def api_trending():
    """Return trending content filtered by type."""
    filter_opt = request.args.get("filter", "semana")

    if filter_opt == "semana":
        last_week = datetime.utcnow() - timedelta(days=7)
        posts = (
            Post.query.join(PostReaction)
            .filter(Post.created_at > last_week)
            .group_by(Post.id)
            .order_by(func.count(PostReaction.id).desc())
            .limit(10)
            .all()
        )
    elif filter_opt == "mes":
        last_month = datetime.utcnow() - timedelta(days=30)
        posts = (
            Post.query.join(PostReaction)
            .filter(Post.created_at > last_month)
            .group_by(Post.id)
            .order_by(func.count(PostReaction.id).desc())
            .limit(10)
            .all()
        )
    elif filter_opt == "populares":
        posts = (
            Post.query.join(PostReaction)
            .group_by(Post.id)
            .order_by(func.count(PostReaction.id).desc())
            .limit(10)
            .all()
        )
    elif filter_opt == "comentarios":
        posts = (
            Post.query.join(PostComment)
            .group_by(Post.id)
            .order_by(func.count(PostComment.id).desc())
            .limit(10)
            .all()
        )
    else:
        posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()

    html = render_template("feed/_trending_posts.html", posts=posts)
    return jsonify({"html": html, "count": len(posts)})


@feed_bp.route("/search")
@activated_required
def search_posts():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    posts = (
        Post.query.filter(Post.content.ilike(f"%{q}%"))
        .order_by(Post.created_at.desc())
        .limit(20)
        .all()
    )
    return jsonify([{"id": p.id, "content": p.content[:100]} for p in posts])


@feed_bp.route("/load")
@activated_required
def load_feed():
    """Return additional feed items for infinite scroll."""
    page = int(request.args.get("page", 1))
    categoria = request.args.get("categoria")

    query = FeedItem.query.options(joinedload(FeedItem.post)).filter_by(
        owner_id=current_user.id
    )
    if categoria == "apuntes":
        query = query.filter_by(item_type="apunte")
    else:
        query = query.filter(FeedItem.item_type != "apunte")

    pagination = query.order_by(FeedItem.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    items = pagination.items
    post_ids = []

    if categoria == "apuntes":
        notes = [i.note for i in items if i.item_type == "apunte" and i.note]
        return render_template("feed/_notes.html", notes=notes) if notes else ""

    posts = [i.post for i in items if i.item_type == "post" and i.post]
    if categoria == "imagen":
        posts = [p for p in posts if p.file_url and not p.file_url.endswith(".pdf")]
    post_ids = [p.id for p in posts]

    if not posts:
        return '<div class="no-more-posts text-center">No hay más publicaciones.</div>'

    reaction_map = PostReaction.counts_for_posts(post_ids)
    user_reactions = PostReaction.reactions_for_user_posts(current_user.id, post_ids)
    from crunevo.models import SavedPost

    saved_posts = {
        sp.post_id: True
        for sp in SavedPost.query.filter(
            SavedPost.user_id == current_user.id,
            SavedPost.post_id.in_(post_ids),
        ).all()
    }

    html = render_template(
        "feed/_posts.html",
        posts=posts,
        reaction_counts=reaction_map,
        user_reactions=user_reactions,
        saved_posts=saved_posts,
    )
    return html
