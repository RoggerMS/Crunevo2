import os
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    jsonify,
    abort,
)
from flask_login import current_user
from crunevo.utils.helpers import activated_required, verified_required
from werkzeug.utils import secure_filename
from crunevo.extensions import db
from crunevo.models import Note, Comment, NoteVote
from crunevo.utils.credits import add_credit
from crunevo.utils import unlock_achievement, send_notification
from crunevo.utils.scoring import update_feed_score
from crunevo.constants import CreditReasons, AchievementCodes
import cloudinary.uploader

notes_bp = Blueprint("notes", __name__, url_prefix="/notes")


@notes_bp.route("/populares")
@activated_required
def popular_notes():
    return redirect(url_for("notes.list_notes", filter="vistos"))


@notes_bp.route("/tag/<string:tag>")
@activated_required
def notes_by_tag(tag):
    return redirect(url_for("notes.list_notes", tag=tag))


@notes_bp.route("/")
@activated_required
def list_notes():
    filter_opt = request.args.get("filter", "recientes")
    tag = request.args.get("tag")

    query = Note.query
    if tag:
        query = query.filter(Note.tags.ilike(f"%{tag}%"))

    if filter_opt == "vistos":
        query = query.order_by(Note.views.desc())
    elif filter_opt == "gustados":
        query = query.order_by(Note.likes.desc())
    else:  # recientes por defecto
        query = query.order_by(Note.created_at.desc())

    notes = query.all()

    # Obtener lista de tags únicos para filtros rápidos
    tag_values = db.session.query(Note.tags).filter(Note.tags != "").all()
    all_tags = set()
    for t in tag_values:
        for tt in t[0].split(","):
            tt = tt.strip()
            if tt:
                all_tags.add(tt)

    return render_template(
        "notes/list.html",
        notes=notes,
        filter=filter_opt,
        categories=sorted(all_tags),
        selected_tag=tag,
    )


@notes_bp.route("/search")
@activated_required
def search_notes():
    q = request.args.get("q", "")
    results = Note.query.filter(
        (Note.title.ilike(f"%{q}%")) | (Note.tags.ilike(f"%{q}%"))
    ).all()
    return jsonify(
        [
            {
                "id": n.id,
                "title": n.title,
                "description": n.description,
                "tags": n.tags,
                "filename": n.filename,
                "views": n.views,
                "likes": n.likes,
            }
            for n in results
        ]
    )


@notes_bp.route("/upload", methods=["GET", "POST"], endpoint="upload_note")
@activated_required
def upload_note():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("El título es obligatorio", "danger")
            return redirect(url_for("notes.upload_note"))

        description = request.form.get("description", "")
        f = request.files.get("file")
        if not f or not f.filename:
            flash("Selecciona un archivo", "danger")
            return redirect(url_for("notes.upload_note"))

        ext = os.path.splitext(f.filename)[1].lower()
        allowed_exts = {".pdf", ".jpg", ".jpeg", ".png"}
        if ext not in allowed_exts:
            flash("El archivo debe ser un PDF o imagen (JPG/PNG)", "danger")
            return redirect(url_for("notes.upload_note"))

        cloud_url = current_app.config.get("CLOUDINARY_URL")
        try:
            if cloud_url:
                filename = secure_filename(f.filename)
                public_id = os.path.splitext(filename)[0]
                if ext == ".pdf":
                    _ = cloudinary.uploader.upload(
                        f,
                        resource_type="auto",
                        public_id=f"notes/{public_id}",
                        format="pdf",
                    )
                    view_url, _ = cloudinary.utils.cloudinary_url(
                        f"notes/{public_id}.pdf",
                        resource_type="image",
                        secure=True,
                    )
                    filepath = view_url
                else:
                    result = cloudinary.uploader.upload(
                        f,
                        resource_type="image",
                        public_id=f"notes/{public_id}",
                    )
                    filepath = result["secure_url"]
            else:
                filename = secure_filename(f.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                f.save(filepath)
        except Exception:
            current_app.logger.exception("Error al subir el archivo")
            flash("Ocurrió un problema al subir el archivo", "danger")
            return redirect(url_for("notes.upload_note"))

        note = Note(
            title=title,
            description=description,
            filename=filepath,
            tags=request.form.get("tags"),
            category=request.form.get("category"),
            author=current_user,
        )
        db.session.add(note)
        current_user.points += 10
        db.session.commit()
        from crunevo.utils import create_feed_item_for_all

        create_feed_item_for_all("apunte", note.id)
        add_credit(current_user, 5, CreditReasons.APUNTE_SUBIDO, related_id=note.id)
        unlock_achievement(current_user, AchievementCodes.PRIMER_APUNTE)
        flash("Apunte subido correctamente")
        return redirect(url_for("notes.list_notes"))

    return render_template("notes/upload.html")


notes_bp.add_url_rule(
    "/upload", endpoint="upload", view_func=upload_note, methods=["GET", "POST"]
)


@notes_bp.route("/<int:note_id>")
@activated_required
def detail(note_id):
    note = Note.query.get_or_404(note_id)
    note.views += 1
    db.session.commit()
    return render_template("notes/detalle.html", note=note)


# Alias endpoint for backward compatibility with templates using
# `notes.view_note` and parameter name `id`.
notes_bp.add_url_rule("/<int:id>", endpoint="view_note", view_func=detail)


@notes_bp.route("/<int:note_id>/comment", methods=["POST"])
@activated_required
def add_comment(note_id):
    note = Note.query.get_or_404(note_id)
    body = request.form["body"]
    comment = Comment(body=body, author=current_user, note=note)
    db.session.add(comment)
    note.comments_count += 1
    db.session.commit()
    if note.user_id != current_user.id:
        send_notification(
            note.user_id,
            f"{current_user.username} comentó tu apunte",
            url_for("notes.view_note", id=note.id),
        )
    update_feed_score(note.id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            {
                "body": comment.body,
                "author": comment.author.username,
                "timestamp": comment.created_at.strftime("%Y-%m-%d %H:%M"),
            }
        )
    return redirect(url_for("notes.view_note", id=note_id))


@notes_bp.route("/<int:note_id>/like", methods=["POST"])
@activated_required
def like_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id == current_user.id:
        abort(403)

    existing_vote = NoteVote.query.filter_by(
        user_id=current_user.id, note_id=note.id
    ).first()

    if existing_vote:
        note.likes = max((note.likes or 0) - 1, 0)
        db.session.delete(existing_vote)
        action = "unliked"
    else:
        note.likes = (note.likes or 0) + 1
        vote = NoteVote(user_id=current_user.id, note_id=note.id)
        db.session.add(vote)
        add_credit(note.author, 1, CreditReasons.VOTO_POSITIVO, related_id=note.id)
        if note.likes >= 100:
            unlock_achievement(note.author, AchievementCodes.LIKE_100)
        action = "liked"

    db.session.commit()
    update_feed_score(note.id)

    if action == "liked" and note.user_id != current_user.id:
        send_notification(
            note.user_id,
            f"{current_user.username} reaccionó a tu apunte",
            url_for("notes.view_note", id=note.id),
        )

    return jsonify({"likes": note.likes, "status": action})


@notes_bp.route("/<int:note_id>/share", methods=["POST"])
@activated_required
def share_note(note_id):
    _note = Note.query.get_or_404(note_id)
    unlock_achievement(current_user, AchievementCodes.COMPARTIDOR)
    flash("¡Gracias por compartir este apunte!")
    return redirect(url_for("notes.view_note", id=note_id))


@notes_bp.route("/<int:note_id>/download")
@verified_required
def download_note(note_id):
    note = Note.query.get_or_404(note_id)
    note.downloads += 1
    db.session.commit()
    update_feed_score(note.id)

    if note.downloads >= 100:
        unlock_achievement(note.author, AchievementCodes.DESCARGA_100)

    return redirect(note.filename)
