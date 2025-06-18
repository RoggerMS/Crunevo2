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
)
from flask_login import current_user
from crunevo.utils.helpers import activated_required
from datetime import datetime
from sqlalchemy import func
from crunevo.extensions import db, csrf
from crunevo.models import (
    Post,
    PostComment,
    FeedItem,
    Note,
    User,
    UserAchievement,
    LoginHistory,
)
from crunevo.forms import FeedNoteForm, FeedImageForm
from crunevo.utils import create_feed_item_for_all, unlock_achievement
from crunevo.utils.credits import add_credit
from crunevo.constants import CreditReasons, AchievementCodes
import redis
from crunevo.cache.feed_cache import fetch as cache_fetch, push_items as cache_push

feed_bp = Blueprint("feed", __name__)
csrf.exempt(feed_bp)


def get_featured_posts():
    """Return top notes, posts and users with recent achievements."""
    top_notes = Note.query.order_by(Note.views.desc()).limit(3).all()
    top_posts = Post.query.order_by(Post.likes.desc()).limit(3).all()
    top_users = (
        db.session.query(User)
        .join(UserAchievement)
        .group_by(User.id)
        .order_by(func.max(UserAchievement.earned_at).desc())
        .limit(3)
        .all()
    )
    return top_notes, top_posts, top_users


def get_weekly_ranking():
    """Return top users of the week and recently earned achievements."""
    from datetime import timedelta, date

    one_week_ago = date.today() - timedelta(days=7)
    top_users = (
        User.query.join(LoginHistory)
        .filter(LoginHistory.login_date >= one_week_ago)
        .group_by(User.id)
        .order_by(User.credits.desc())
        .limit(3)
        .all()
    )

    recent_achievements = (
        db.session.query(User.username, UserAchievement.badge_code)
        .join(UserAchievement)
        .order_by(UserAchievement.earned_at.desc())
        .limit(5)
        .all()
    )

    return top_users, recent_achievements


@feed_bp.route("/feed", methods=["GET", "POST"])
@activated_required
def edu_feed():
    note_form = FeedNoteForm()
    image_form = FeedImageForm()

    if note_form.validate_on_submit() and request.form.get("form_type") == "note":
        f = note_form.file.data
        filepath = ""
        if f and f.filename:
            cloud_url = current_app.config.get("CLOUDINARY_URL")
            if cloud_url:
                result = cloudinary.uploader.upload(f)
                filepath = result["secure_url"]
            else:
                filename = secure_filename(f.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                f.save(filepath)

        note = Note(
            title=note_form.title.data,
            description=note_form.summary.data,
            filename=filepath,
            tags=note_form.tags.data,
            author=current_user,
        )
        db.session.add(note)
        current_user.points += 10
        db.session.commit()
        create_feed_item_for_all("apunte", note.id)
        add_credit(current_user, 5, CreditReasons.APUNTE_SUBIDO, related_id=note.id)
        unlock_achievement(current_user, AchievementCodes.PRIMER_APUNTE)
        flash("Apunte publicado")
        return redirect(url_for("feed.edu_feed"))

    if image_form.validate_on_submit() and request.form.get("form_type") == "image":
        image = image_form.image.data
        file_url = None
        if image and image.filename:
            cloud_url = current_app.config.get("CLOUDINARY_URL")
            if cloud_url:
                result = cloudinary.uploader.upload(image, resource_type="auto")
                file_url = result["secure_url"]
            else:
                filename = secure_filename(image.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                image.save(filepath)
                file_url = filepath

        post = Post(
            content=image_form.title.data or "",
            file_url=file_url,
            author=current_user,
        )
        db.session.add(post)
        db.session.commit()
        create_feed_item_for_all("post", post.id)
        flash("Publicación creada")
        return redirect(url_for("feed.edu_feed"))

    feed_items_raw = FeedItem.query.order_by(FeedItem.created_at.desc()).limit(20).all()
    feed_items = []
    for item in feed_items_raw:
        if item.item_type == "apunte":
            note = Note.query.get(item.ref_id)
            if note:
                feed_items.append({"type": "note", "data": note})
        elif item.item_type == "post":
            post = Post.query.get(item.ref_id)
            if post:
                feed_items.append({"type": "post", "data": post})

    return render_template(
        "feed/list.html",
        feed_items=feed_items,
        note_form=note_form,
        image_form=image_form,
    )


@feed_bp.route("/", methods=["GET", "POST"])
@activated_required
def index():
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if not content:
            flash("Debes escribir algo", "danger")
            return redirect(url_for("feed.index"))

        file = request.files.get("file")
        file_url = None
        if file and file.filename:
            cloud_url = current_app.config.get("CLOUDINARY_URL")
            try:
                if cloud_url:
                    res = cloudinary.uploader.upload(file, resource_type="auto")
                    file_url = res["secure_url"]
                else:
                    filename = secure_filename(file.filename)
                    upload_folder = current_app.config["UPLOAD_FOLDER"]
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    file_url = filepath
            except Exception:
                current_app.logger.exception("Error al subir archivo")
                flash("Ocurrió un problema al subir el archivo", "danger")
                return redirect(url_for("feed.index"))

        post = Post(content=content, file_url=file_url, author=current_user)
        db.session.add(post)
        db.session.commit()
        create_feed_item_for_all("post", post.id)
        flash("Publicación creada")
        return redirect(url_for("feed.index"))

    posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    top_notes, top_posts, top_users = get_featured_posts()
    top_ranked, recent_achievements = get_weekly_ranking()
    return render_template(
        "feed/feed.html",
        posts=posts,
        top_notes=top_notes,
        top_posts=top_posts,
        top_users=top_users,
        top_ranked=top_ranked,
        recent_achievements=recent_achievements,
    )


@feed_bp.route("/trending")
@activated_required
def trending():
    posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    today = datetime.utcnow().date()
    return render_template("feed/feed.html", posts=posts, trending=True, today=today)


@feed_bp.route("/post/<int:post_id>", endpoint="view_post")
@activated_required
def view_post(post_id: int):
    """Display a single post."""
    post = Post.query.get_or_404(post_id)
    return render_template("feed/post_detail.html", post=post)


# Alias route for backwards compatibility
feed_bp.add_url_rule("/posts/<int:post_id>", endpoint="view_post", view_func=view_post)


@feed_bp.route("/like/<int:post_id>", methods=["POST"])
@activated_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.likes is None:
        post.likes = 0
    post.likes += 1
    db.session.commit()
    return jsonify({"likes": post.likes})


@feed_bp.route("/comment/<int:post_id>", methods=["POST"])
@activated_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    body = request.form.get("body", "").strip()
    if not body:
        return jsonify({"error": "Comentario vacío"}), 400
    comment = PostComment(body=body, author=current_user, post=post)
    db.session.add(comment)
    db.session.commit()
    return jsonify(
        {
            "body": comment.body,
            "author": comment.author.username,
            "timestamp": comment.timestamp.strftime("%Y-%m-%d %H:%M"),
        }
    )


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
    start = (page - 1) * 10
    stop = start + 9
    try:
        items = cache_fetch(current_user.id, start, stop)
    except redis.RedisError:
        items = []
    if not items:
        q = (
            FeedItem.query.filter_by(owner_id=current_user.id)
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
    return jsonify(items)
