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
from crunevo.extensions import db, csrf
from crunevo.models import Post, FeedItem, Note
from crunevo.forms import FeedNoteForm, FeedImageForm
from crunevo.utils import create_feed_item_for_all, unlock_achievement
from crunevo.utils.credits import add_credit
from crunevo.constants import CreditReasons, AchievementCodes
import redis
from crunevo.cache.feed_cache import fetch as cache_fetch, push_items as cache_push

feed_bp = Blueprint("feed", __name__)
csrf.exempt(feed_bp)


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
        image_url = None
        if image and image.filename:
            cloud_url = current_app.config.get("CLOUDINARY_URL")
            if cloud_url:
                result = cloudinary.uploader.upload(image)
                image_url = result["secure_url"]
            else:
                filename = secure_filename(image.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                image.save(filepath)
                image_url = filepath

        post = Post(
            content=image_form.title.data or "",
            image_url=image_url,
            author=current_user,
        )
        db.session.add(post)
        db.session.commit()
        create_feed_item_for_all("post", post.id)
        flash("Publicación creada")
        return redirect(url_for("feed.edu_feed"))

    page = request.args.get("page", 1, type=int)
    per_page = 10
    pagination = Note.query.order_by(Note.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    notes = pagination.items
    return render_template(
        "feed/list.html",
        notes=notes,
        pagination=pagination,
        note_form=note_form,
        image_form=image_form,
    )


@feed_bp.route("/", methods=["GET", "POST"])
@activated_required
def index():
    if request.method == "POST":
        content = request.form["content"]
        image = request.files.get("image")
        image_url = None
        if image and image.filename:
            cloud_url = current_app.config.get("CLOUDINARY_URL")
            if cloud_url:
                result = cloudinary.uploader.upload(image)
                image_url = result["secure_url"]
            else:
                filename = secure_filename(image.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                image.save(filepath)
                image_url = filepath
        post = Post(content=content, image_url=image_url, author=current_user)
        db.session.add(post)
        db.session.commit()
        from crunevo.utils import create_feed_item_for_all

        create_feed_item_for_all("post", post.id)
        flash("Publicación creada")
        return redirect(url_for("feed.index"))
    return render_template("feed/index.html")


@feed_bp.route("/trending")
@activated_required
def trending():
    posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    today = datetime.utcnow().date()
    return render_template("feed/feed.html", posts=posts, trending=True, today=today)


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
