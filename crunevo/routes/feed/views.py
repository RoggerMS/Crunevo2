import os
import cloudinary.uploader
from werkzeug.utils import secure_filename
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    abort,
)
from flask_login import current_user

from crunevo.extensions import db
from crunevo.models import (
    Post,
    PostImage,
    PostComment,
    PostReaction,
    FeedItem,
    Note,
    User,
    Report,
)
from crunevo.utils.helpers import activated_required
from crunevo.utils import (
    create_feed_item_for_all,
    send_notification,
    record_activity,
)
from crunevo.cache.feed_cache import remove_item
from sqlalchemy.exc import IntegrityError
from crunevo.services.feed_service import (
    fetch_feed_data,
    streak_info,
    get_weekly_top_posts,
    get_featured_posts,
    get_weekly_ranking,
)

from . import feed_bp


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
    data = fetch_feed_data(current_user, categoria)
    streak, show_streak, reward = streak_info(current_user)

    template = "feed/feed.html"
    return render_template(
        template,
        feed_items=data["feed_items"],
        categoria=categoria,
        reaction_counts=data["reaction_counts"],
        user_reactions=data["user_reactions"],
        saved_posts=data["saved_posts"],
        show_streak_claim=show_streak,
        trending_posts=data["trending_posts"],
        trending_counts=data["trending_counts"],
        trending_user_reactions=data["trending_user_reactions"],
        streak_day=streak.current_day if streak else 1,
        streak_reward=reward,
    )


# Alias route for backwards compatibility
feed_home = view_feed
feed_bp.add_url_rule(
    "/",
    endpoint="feed_home",
    view_func=view_feed,
    methods=["GET", "POST"],
)


@feed_bp.route("/trending")
def trending():
    weekly_posts = get_weekly_top_posts(limit=10)
    top_ranked, recent_achievements = get_weekly_ranking()
    top_notes, top_posts, top_users = get_featured_posts()

    # Popular forum questions ordered by answers and views
    try:
        from crunevo.models.forum import ForumQuestion, ForumAnswer
        from sqlalchemy import func

        top_questions_query = (
            db.session.query(
                ForumQuestion, func.count(ForumAnswer.id).label("answer_count")
            )
            .outerjoin(ForumAnswer)
            .group_by(ForumQuestion.id)
            .order_by(func.count(ForumAnswer.id).desc(), ForumQuestion.views.desc())
            .limit(5)
            .all()
        )

        # Add answer_count as attribute to each question
        top_questions = []
        for question, answer_count in top_questions_query:
            question.answer_count = answer_count
            top_questions.append(question)
    except Exception:
        current_app.logger.exception("Error loading forum questions for trending")
        top_questions = []

    reaction_map = PostReaction.counts_for_posts([p.id for p in weekly_posts])
    if current_user.is_authenticated:
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
    else:
        user_reactions = {}
        saved_posts = {}

    return render_template(
        "feed/trending.html",
        weekly_posts=weekly_posts,
        top_ranked=top_ranked,
        recent_achievements=recent_achievements,
        top_notes=top_notes,
        top_posts=top_posts,
        top_users=top_users,
        top_questions=top_questions,
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
    PostReaction.query.filter_by(post_id=post.id).delete()
    PostComment.query.filter_by(post_id=post.id).delete()
    PostImage.query.filter_by(post_id=post.id).delete()
    try:
        from crunevo.models import SavedPost

        SavedPost.query.filter_by(post_id=post.id).delete()
    except Exception:
        current_app.logger.exception("Error deleting saved post")
    db.session.delete(post)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(
            "No se pudo eliminar la publicación por registros relacionados",
            "danger",
        )
        return redirect(url_for("feed.view_post", post_id=post.id))
    for uid in owner_ids:
        try:
            remove_item(uid, "post", post.id)
        except Exception:
            current_app.logger.exception("Error removing item from feed cache")
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
