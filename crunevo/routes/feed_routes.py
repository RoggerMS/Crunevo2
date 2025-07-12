import os
import cloudinary.uploader
from werkzeug.utils import secure_filename
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    current_app,
    abort,
)
from flask_login import current_user
from crunevo.utils.helpers import activated_required
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from crunevo.extensions import db, csrf
from datetime import date
from crunevo.utils.login_streak import streak_reward
from crunevo.models import (
    Post,
    PostImage,
    PostComment,
    PostReaction,
    FeedItem,
    Note,
    User,
    UserAchievement,
    Credit,
    Report,
)
from crunevo.utils import (
    create_feed_item_for_all,
    send_notification,
    record_activity,
)
from crunevo.utils.credits import add_credit, spend_credit
from crunevo.constants import CreditReasons
from crunevo.cache.feed_cache import (
    fetch as cache_fetch,
    push_items as cache_push,
    remove_item,
)
from sqlalchemy.exc import IntegrityError

feed_bp = Blueprint("feed", __name__, url_prefix="/feed")
csrf.exempt(feed_bp)


def get_featured_posts():
    """Return top notes, posts and users with recent achievements."""
    top_notes = Note.query.order_by(Note.views.desc()).limit(3).all()
    top_posts = Post.query.order_by(Post.likes.desc()).limit(3).all()
    top_users = (
        db.session.query(User)
        .join(UserAchievement)
        .group_by(User.id)
        .order_by(func.max(UserAchievement.timestamp).desc())
        .limit(3)
        .all()
    )
    return top_notes, top_posts, top_users


def get_weekly_top_posts(limit=3):
    """Return posts with most likes from the last week."""
    from datetime import datetime, timedelta

    last_week = datetime.utcnow() - timedelta(days=7)
    return (
        Post.query.filter(Post.created_at > last_week)
        .order_by(Post.likes.desc())
        .limit(limit)
        .all()
    )


def get_weekly_ranking(limit=5):
    now = datetime.utcnow()
    week_start = now - timedelta(days=7)
    top_ranked = (
        db.session.query(
            User.username,
            func.coalesce(func.sum(Credit.amount), 0).label("credits"),
        )
        .join(Credit, Credit.user_id == User.id)
        .filter(Credit.timestamp >= week_start)
        .group_by(User.id)
        .order_by(desc("credits"))
        .limit(limit)
        .all()
    )

    recent_achievements = (
        db.session.query(
            User.username, UserAchievement.badge_code, UserAchievement.timestamp
        )
        .join(User, User.id == UserAchievement.user_id)
        .order_by(UserAchievement.timestamp.desc())
        .limit(limit)
        .all()
    )
    return top_ranked, recent_achievements


@feed_bp.route("/post", methods=["POST"], endpoint="create_post")
@activated_required
def create_post():
    """Create a new feed post."""
    content = request.form.get("content", "").strip()
    comment_permission = request.form.get("comment_permission", "all")
    files = request.files.getlist("files") or request.files.getlist("file")

    valid_files = [f for f in files if f and f.filename]

    if not content and not valid_files:
        flash("Debes escribir algo", "danger")
        return redirect(url_for("feed.view_feed"))

    urls = []
    for f in valid_files:
        cloud_url = current_app.config.get("CLOUDINARY_URL")
        try:
            if cloud_url:
                res = cloudinary.uploader.upload(f, resource_type="auto")
                urls.append(res["secure_url"])
            else:
                filename = secure_filename(f.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                f.save(filepath)
                urls.append(filepath)
        except Exception:
            current_app.logger.exception("Error al subir archivo")
            flash("Ocurrió un problema al subir el archivo", "danger")
            return redirect(url_for("feed.view_feed"))

    comment_permission = request.form.get("comment_permission", "all")
    post = Post(
        content=content,
        file_url=urls[0] if urls else None,
        author=current_user,
        comment_permission=comment_permission,
    )
    db.session.add(post)
    db.session.flush()
    for url in urls:
        db.session.add(PostImage(post_id=post.id, url=url))
    db.session.commit()
    record_activity("post_created", post.id, "post")
    create_feed_item_for_all("post", post.id)
    flash("Publicación creada")
    return redirect(url_for("feed.view_feed"))


@feed_bp.route("/", methods=["GET", "POST"], endpoint="view_feed")
@activated_required
def view_feed():
    if request.method == "POST":
        return create_post()

    categoria = request.args.get("categoria")
    query = FeedItem.query.filter_by(owner_id=current_user.id)
    if categoria == "apuntes":
        query = query.filter_by(item_type="apunte")
    else:
        query = query.filter(FeedItem.item_type != "apunte")
    feed_items_raw = query.order_by(FeedItem.created_at.desc()).limit(20).all()

    feed_items = []
    post_ids = []
    for item in feed_items_raw:
        if item.item_type == "post":
            post = Post.query.get(item.ref_id)
            if categoria == "imagen" and (
                not post or not post.file_url or post.file_url.endswith(".pdf")
            ):
                continue
            if post:
                feed_items.append({"type": "post", "data": post})
                post_ids.append(post.id)
        elif item.item_type == "apunte" and categoria == "apuntes":
            note = Note.query.get(item.ref_id)
            if note:
                feed_items.append({"type": "note", "data": note})

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
    trending_posts = get_weekly_top_posts(limit=3)
    trending_counts = PostReaction.counts_for_posts([p.id for p in trending_posts])
    trending_user_reactions = PostReaction.reactions_for_user_posts(
        current_user.id, [p.id for p in trending_posts]
    )

    streak = current_user.login_streak
    show_streak = (
        streak
        and streak.last_login == date.today()
        and streak.claimed_today != date.today()
    )
    reward = streak_reward(streak.current_day) if streak else 0

    template = "feed/feed.html"
    return render_template(
        template,
        feed_items=feed_items,
        categoria=categoria,
        reaction_counts=reaction_map,
        user_reactions=user_reactions,
        saved_posts=saved_posts,
        show_streak_claim=show_streak,
        trending_posts=trending_posts,
        trending_counts=trending_counts,
        trending_user_reactions=trending_user_reactions,
        streak_day=streak.current_day if streak else 1,
        streak_reward=reward,
    )


# Alias route for backwards compatibility
feed_bp.add_url_rule(
    "/", endpoint="feed_home", view_func=view_feed, methods=["GET", "POST"]
)
# Legacy endpoint for older templates/tests
feed_bp.add_url_rule("/", endpoint="feed", view_func=view_feed, methods=["GET", "POST"])

# Expose alias for imports
feed_home = view_feed


@feed_bp.route("/trending")
@activated_required
def trending():
    weekly_posts = get_weekly_top_posts(limit=10)
    top_ranked, recent_achievements = get_weekly_ranking()
    top_notes, top_posts, top_users = get_featured_posts()

    reaction_map = PostReaction.counts_for_posts([p.id for p in weekly_posts])
    user_reactions = PostReaction.reactions_for_user_posts(
        current_user.id, [p.id for p in weekly_posts]
    )
    from crunevo.models import SavedPost

    saved_posts = {
        sp.post_id: True
        for sp in SavedPost.query.filter(
            SavedPost.user_id == current_user.id,
            SavedPost.post_id.in_([p.id for p in weekly_posts]),
        ).all()
    }

    return render_template(
        "feed/trending.html",
        weekly_posts=weekly_posts,
        top_ranked=top_ranked,
        recent_achievements=recent_achievements,
        top_notes=top_notes,
        top_posts=top_posts,
        top_users=top_users,
        reaction_counts=reaction_map,
        user_reactions=user_reactions,
        saved_posts=saved_posts,
    )


@feed_bp.route("/post/<int:post_id>", endpoint="view_post_bp")
@activated_required
def view_post(post_id: int):
    """Display a single post."""
    post = Post.query.get_or_404(post_id)
    counts = PostReaction.count_for_post(post.id)
    my_reaction = (
        PostReaction.query.with_entities(PostReaction.reaction_type)
        .filter_by(user_id=current_user.id, post_id=post.id)
        .scalar()
    )
    og_title = (
        f"Publicación de {post.author.username}"
        if post.author
        else "Publicación en Crunevo"
    )
    og_description = (post.content or "")[:100]
    return render_template(
        "feed/post_detail.html",
        post=post,
        reaction_counts=counts,
        user_reaction=my_reaction,
        og_title=og_title,
        og_description=og_description,
    )


@feed_bp.route("/post/<int:post_id>/photo/<int:index>", endpoint="view_post_photo")
def view_post_photo(post_id: int, index: int):
    """Display a single image from a post."""
    post = Post.query.get_or_404(post_id)
    counts = PostReaction.count_for_post(post.id)
    my_reaction = (
        PostReaction.query.with_entities(PostReaction.reaction_type)
        .filter_by(user_id=current_user.id, post_id=post.id)
        .scalar()
    )
    image_url = None
    if post.images and 1 <= index <= len(post.images):
        image_url = post.images[index - 1].url
    elif post.file_url:
        image_url = post.file_url
    og_title = f"Foto de {post.author.username}" if post.author else "Foto en Crunevo"
    og_description = (post.content or "")[:100]
    return render_template(
        "feed/post_detail.html",
        post=post,
        reaction_counts=counts,
        user_reaction=my_reaction,
        og_image=image_url,
        og_title=og_title,
        og_description=og_description,
        photo_index=index,
    )


@feed_bp.route("/user/<int:user_id>/posts")
@activated_required
def user_posts(user_id: int):
    """List posts from a specific user."""
    user = User.query.get_or_404(user_id)
    page = request.args.get("page", 1, type=int)
    pagination = (
        Post.query.filter_by(author_id=user.id)
        .order_by(Post.created_at.desc())
        .paginate(page=page, per_page=10)
    )
    posts = pagination.items
    post_ids = [p.id for p in posts]
    reaction_map = PostReaction.counts_for_posts(post_ids)
    user_reactions = PostReaction.reactions_for_user_posts(current_user.id, post_ids)
    feed_items = [{"type": "post", "data": p} for p in posts]
    trending_posts = get_weekly_top_posts(limit=3)
    trending_counts = PostReaction.counts_for_posts([p.id for p in trending_posts])
    trending_user_reactions = PostReaction.reactions_for_user_posts(
        current_user.id, [p.id for p in trending_posts]
    )
    return render_template(
        "feed/feed.html",
        feed_items=feed_items,
        categoria=None,
        reaction_counts=reaction_map,
        user_reactions=user_reactions,
        pagination=pagination,
        show_streak_claim=False,
        trending_posts=trending_posts,
        trending_counts=trending_counts,
        trending_user_reactions=trending_user_reactions,
        viewed_user=user,
    )


@feed_bp.route("/apuntes/user/<int:user_id>")
@activated_required
def user_notes(user_id: int):
    """List notes from a specific user."""
    user = User.query.get_or_404(user_id)
    page = request.args.get("page", 1, type=int)
    pagination = (
        Note.query.filter_by(user_id=user.id)
        .order_by(Note.created_at.desc())
        .paginate(page=page, per_page=10)
    )
    notes = pagination.items
    return render_template(
        "feed/user_notes.html", user=user, notes=notes, pagination=pagination
    )


# Alias route for backwards compatibility
feed_bp.add_url_rule(
    "/posts/<int:post_id>", endpoint="view_post_bp", view_func=view_post
)


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
            # remove reaction
            db.session.delete(existing)
            post.likes = max((post.likes or 0) - 1, 0)
            action = "removed"
        else:
            # change reaction type
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
        post.likes = (post.likes or 0) + 1
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
    return jsonify({"likes": post.likes, "counts": counts, "status": action})


@feed_bp.route("/comment/<int:post_id>", methods=["POST"])
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.comment_permission == "none" and post.author_id != current_user.id:
        return jsonify({"error": "Comentarios deshabilitados"}), 403
    if post.comment_permission == "friends" and post.author_id != current_user.id:
        if hasattr(post.author, "is_friend") and not post.author.is_friend(
            current_user
        ):
            return jsonify({"error": "Solo amigos pueden comentar"}), 403
    body = request.form.get("body", "").strip()
    if not body:
        return jsonify({"error": "Comentario vacío"}), 400
    if current_user.is_authenticated:
        comment = PostComment(body=body, author=current_user, post=post)
    else:
        comment = PostComment(body=body, post=post, pending=True)
    db.session.add(comment)
    db.session.commit()
    if current_user.is_authenticated:
        record_activity("comment_post", comment.id, "post")
        if post.author_id != current_user.id:
            send_notification(
                post.author_id,
                f"{current_user.username} comentó tu publicación",
                url_for("feed.view_post", post_id=post.id),
            )
        return jsonify(
            {
                "body": comment.body,
                "author": comment.author.username,
                "timestamp": comment.timestamp.strftime("%Y-%m-%d %H:%M"),
            }
        )
    return jsonify({"pending": True}), 202


@feed_bp.route("/api/comments/<int:post_id>")
@activated_required
def api_comments(post_id):
    """Return recent comments for a post."""
    post = Post.query.get_or_404(post_id)
    comments = (
        PostComment.query.filter_by(post_id=post.id, pending=False)
        .order_by(PostComment.timestamp.desc())
        .limit(50)
        .all()
    )
    return jsonify(
        [
            {
                "body": c.body,
                "author": c.author.username,
                "avatar": c.author.avatar_url
                or url_for("static", filename="img/default.png"),
                "timestamp": c.timestamp.isoformat(),
            }
            for c in comments
        ]
    )


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
    html = render_template(
        "feed/_post_modal.html",
        post=post,
        reaction_counts=counts,
        user_reaction=my_reaction,
        saved_posts={post.id: saved},
    )
    return jsonify({"html": html})


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


@feed_bp.route("/post/editar/<int:post_id>", methods=["POST"], endpoint="editar_post")
@activated_required
def editar_post(post_id):
    """Edit a post's content if the current user is the author."""
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id:
        abort(403)
    content = request.form.get("content", "").strip()
    comment_permission = request.form.get("comment_permission", post.comment_permission)
    if not content:
        flash("El contenido no puede estar vacío", "danger")
        return redirect(url_for("feed.view_post", post_id=post.id))
    updated = False
    if content != post.content:
        post.content = content
        post.edited = True
        updated = True
    if comment_permission != post.comment_permission:
        post.comment_permission = comment_permission
        updated = True
    if updated:
        db.session.commit()
    flash("Publicación actualizada", "success")
    return redirect(url_for("feed.view_post", post_id=post.id))


@feed_bp.route("/post/eliminar/<int:post_id>", methods=["POST"])
@activated_required
def eliminar_post(post_id):
    """Delete a post and related feed items."""
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id:
        abort(403)
    feed_items = FeedItem.query.filter_by(item_type="post", ref_id=post.id).all()
    owner_ids = [fi.owner_id for fi in feed_items]
    FeedItem.query.filter_by(item_type="post", ref_id=post.id).delete()
    try:
        from crunevo.models import SavedPost

        SavedPost.query.filter_by(post_id=post.id).delete()
    except Exception:
        pass
    db.session.delete(post)
    db.session.commit()
    for uid in owner_ids:
        try:
            remove_item(uid, "post", post.id)
        except Exception:
            pass
    flash("Publicación eliminada correctamente", "success")
    return redirect(url_for("feed.view_feed"))


@feed_bp.route("/post/reportar/<int:post_id>", methods=["POST"], endpoint="report_post")
@activated_required
def report_post(post_id):
    """Allow users to report a post."""
    post = Post.query.get_or_404(post_id)
    if post.author_id == current_user.id:
        abort(403)
    reason = request.form.get("reason", "").strip()
    report = Report(
        user_id=current_user.id,
        description=f"Post {post_id}: {reason}",
    )
    db.session.add(report)
    admin = User.query.filter_by(role="admin").first()
    if admin:
        send_notification(admin.id, f"Nuevo reporte de post {post_id}")
    db.session.commit()
    flash("Publicación reportada", "success")
    return redirect(url_for("feed.view_post", post_id=post.id))


@feed_bp.route("/api/chat", methods=["POST"])
@activated_required
def api_chat():
    question = request.json.get("question")
    # placeholder for future AI integration
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

    # Remove duplicate posts by ref_id while preserving order
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
        query = query.order_by(Post.likes.desc())
    elif filter_opt == "relevantes":
        week_start = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Post.created_at >= week_start).order_by(Post.likes.desc())
    else:  # recientes or publicaciones
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
        from datetime import datetime, timedelta

        last_week = datetime.utcnow() - timedelta(days=7)
        posts = (
            Post.query.filter(Post.created_at > last_week)
            .order_by(Post.likes.desc())
            .limit(10)
            .all()
        )
    elif filter_opt == "mes":
        from datetime import datetime, timedelta

        last_month = datetime.utcnow() - timedelta(days=30)
        posts = (
            Post.query.filter(Post.created_at > last_month)
            .order_by(Post.likes.desc())
            .limit(10)
            .all()
        )
    elif filter_opt == "populares":
        posts = Post.query.order_by(Post.likes.desc()).limit(10).all()
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
