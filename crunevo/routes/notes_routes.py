import os
import json
import subprocess
import tempfile
from urllib.parse import urlparse
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
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from crunevo.extensions import db, talisman, oauth
from flask import session
from crunevo.models import (
    Note,
    Comment,
    NoteVote,
    FeedItem,
    Credit,
    Report,
    User,
    Referral,
    PrintRequest,
)
from crunevo.utils.credits import add_credit
from crunevo.utils import (
    unlock_achievement,
    send_notification,
    record_activity,
    suggest_categories,
    translate_fields,
)
from crunevo.utils.scoring import update_feed_score
from crunevo.cache.feed_cache import remove_item
from crunevo.constants import CreditReasons, AchievementCodes
from crunevo.app import DEFAULT_CSP
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
        category = request.form.get("category", "")
        valid_categories = current_app.config.get("NOTE_CATEGORIES", [])
        if valid_categories and category not in valid_categories:
            flash("Categoría inválida", "danger")
            return redirect(url_for("notes.upload_note"))
        files = request.files.getlist("file")
        if len(files) != 1 or not files[0].filename:
            flash("Selecciona un único archivo", "danger")
            return redirect(url_for("notes.upload_note"))
        f = files[0]

        ext = os.path.splitext(f.filename)[1].lower()
        allowed_exts = {".pdf", ".jpg", ".jpeg", ".png", ".docx", ".pptx"}
        if ext not in allowed_exts:
            flash(
                "Formato no soportado. Usa PDF, imagen, Word o PowerPoint",
                "danger",
            )
            return redirect(url_for("notes.upload_note"))

        if ext == ".pdf":
            ftype = "pdf"
        elif ext in {".jpg", ".jpeg", ".png", ".webp"}:
            ftype = "image"
        elif ext == ".docx":
            ftype = "docx"
        elif ext == ".pptx":
            ftype = "pptx"
        else:
            ftype = "other"

        from crunevo.utils import plagiarism

        file_hash = plagiarism.compute_hash(f.stream)
        duplicate_id = plagiarism.get_duplicate(file_hash)
        if duplicate_id:
            report = Report(
                user_id=current_user.id,
                description=f"Duplicate note attempt matches {duplicate_id}",
            )
            db.session.add(report)
            admin = User.query.filter_by(role="admin").first()
            if admin:
                send_notification(
                    admin.id,
                    f"Posible plagio al subir nota coincidente con {duplicate_id}",
                )
            db.session.commit()
            flash(
                "El archivo parece ser una copia de otro apunte y se revisará.",
                "danger",
            )
            return redirect(url_for("notes.upload_note"))

        cloud_url = current_app.config.get("CLOUDINARY_URL")
        original_url = ""
        try:
            if cloud_url:
                filename = secure_filename(f.filename)
                public_id = os.path.splitext(filename)[0]
                if ext == ".pdf":
                    result = cloudinary.uploader.upload(
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
                    original_url = result["secure_url"]
                elif ext == ".docx":
                    tmpdir = tempfile.mkdtemp()
                    tmp_path = os.path.join(tmpdir, filename)
                    f.save(tmp_path)
                    result = cloudinary.uploader.upload(
                        tmp_path,
                        resource_type="raw",
                        public_id=f"notes/{public_id}",
                        format="docx",
                    )
                    filepath = result["secure_url"]
                    original_url = filepath
                elif ext == ".pptx":
                    tmpdir = tempfile.mkdtemp()
                    tmp_path = os.path.join(tmpdir, filename)
                    f.save(tmp_path)
                    orig = cloudinary.uploader.upload(
                        tmp_path,
                        resource_type="raw",
                        public_id=f"notes/{public_id}",
                        format="pptx",
                    )
                    subprocess.run(
                        [
                            "soffice",
                            "--headless",
                            "--convert-to",
                            "pdf",
                            "--outdir",
                            tmpdir,
                            tmp_path,
                        ],
                        check=True,
                    )
                    pdf_path = os.path.join(
                        tmpdir, os.path.splitext(filename)[0] + ".pdf"
                    )
                    _ = cloudinary.uploader.upload(
                        pdf_path,
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
                    original_url = orig["secure_url"]
                else:
                    result = cloudinary.uploader.upload(
                        f,
                        resource_type="image",
                        public_id=f"notes/{public_id}",
                    )
                    filepath = result["secure_url"]
                    original_url = filepath
            else:
                filename = secure_filename(f.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                f.save(filepath)
                original_url = filepath
                if ext == ".pptx":
                    subprocess.run(
                        [
                            "soffice",
                            "--headless",
                            "--convert-to",
                            "pdf",
                            "--outdir",
                            upload_folder,
                            filepath,
                        ],
                        check=True,
                    )
                    filepath = os.path.join(
                        upload_folder, os.path.splitext(filename)[0] + ".pdf"
                    )
        except Exception:
            current_app.logger.exception("Error al subir el archivo")
            flash("Ocurrió un problema al subir el archivo", "danger")
            return redirect(url_for("notes.upload_note"))

        if not category:
            cats = current_app.config.get("NOTE_CATEGORIES", [])
            suggested = suggest_categories(f"{title} {description}", cats)
            if suggested:
                category = suggested[0]

        note = Note(
            title=title,
            description=description,
            filename=filepath,
            original_file_url=original_url,
            file_type=ftype,
            tags=request.form.get("tags"),
            category=category,
            language=request.form.get("language"),
            reading_time=request.form.get("reading_time"),
            content_type=request.form.get("content_type"),
            summary=request.form.get("summary"),
            course=request.form.get("course"),
            career=request.form.get("career"),
            author=current_user,
        )
        db.session.add(note)
        current_user.points += 10
        db.session.commit()
        plagiarism.record_hash(note.id, file_hash)
        from crunevo.utils import create_feed_item_for_all

        create_feed_item_for_all("apunte", note.id)
        trans_folder = os.path.join(current_app.config["TRANSLATIONS_FOLDER"], "notes")
        langs = current_app.config.get("NOTE_TRANSLATION_LANGS", ["en"])
        translate_fields(note.id, note.title, note.description, langs, trans_folder)
        add_credit(current_user, 5, CreditReasons.APUNTE_SUBIDO, related_id=note.id)
        unlock_achievement(current_user, AchievementCodes.PRIMER_APUNTE)
        ref = None
        try:
            ref = Referral.query.filter_by(
                invitado_id=current_user.id, completado=True
            ).first()
        except Exception:
            db.session.rollback()
        if ref:
            unlock_achievement(ref.invitador, AchievementCodes.ALIADO_EDUCATIVO)
        flash("Apunte subido correctamente")
        return redirect(url_for("notes.list_notes"))

    return render_template(
        "notes/upload.html",
        suggestions=current_app.config.get("TAG_SUGGESTIONS", []),
        categories=current_app.config.get("NOTE_CATEGORIES", []),
    )


notes_bp.add_url_rule(
    "/upload", endpoint="upload", view_func=upload_note, methods=["GET", "POST"]
)


@notes_bp.route("/import/drive")
@activated_required
def drive_authorize():
    redirect_uri = url_for("notes.drive_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@notes_bp.route("/import/drive/callback")
@activated_required
def drive_callback():
    token = oauth.google.authorize_access_token()
    session["drive_token"] = token
    resp = oauth.google.get(
        "drive/v3/files",
        params={"pageSize": 20, "fields": "files(id,name,mimeType)"},
    )
    files = resp.json().get("files", [])
    return render_template("notes/import_list.html", files=files, source="drive")


@notes_bp.route("/import/dropbox")
@activated_required
def dropbox_authorize():
    redirect_uri = url_for("notes.dropbox_callback", _external=True)
    return oauth.dropbox.authorize_redirect(redirect_uri)


@notes_bp.route("/import/dropbox/callback")
@activated_required
def dropbox_callback():
    token = oauth.dropbox.authorize_access_token()
    session["dropbox_token"] = token
    resp = oauth.dropbox.post("files/list_folder", json={"path": ""})
    entries = resp.json().get("entries", [])
    files = [e for e in entries if e.get(".tag") != "folder"]
    return render_template("notes/import_list.html", files=files, source="dropbox")


@notes_bp.route(
    "/import/<string:source>/<path:file_id>", methods=["POST"], endpoint="import_file"
)
@activated_required
def import_file(source, file_id):
    if source == "drive":
        token = session.get("drive_token")
        if not token:
            abort(403)
        meta = oauth.google.get(
            f"drive/v3/files/{file_id}", params={"fields": "name"}
        ).json()
        name = meta.get("name", file_id)
        res = oauth.google.get(f"drive/v3/files/{file_id}", params={"alt": "media"})
    elif source == "dropbox":
        token = session.get("dropbox_token")
        if not token:
            abort(403)
        meta = oauth.dropbox.post("files/get_metadata", json={"path": file_id}).json()
        name = meta.get("name", file_id)
        res = oauth.dropbox.post(
            "files/download",
            headers={"Dropbox-API-Arg": json.dumps({"path": file_id})},
        )
    else:
        abort(404)

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(name)
    path = os.path.join(upload_folder, filename)
    with open(path, "wb") as f:
        f.write(res.content)

    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        ftype = "pdf"
    elif ext in {".jpg", ".jpeg", ".png", ".webp"}:
        ftype = "image"
    elif ext == ".docx":
        ftype = "docx"
    elif ext == ".pptx":
        ftype = "pptx"
    else:
        ftype = "other"

    note = Note(title=name, filename=path, file_type=ftype, author=current_user)
    db.session.add(note)
    db.session.commit()
    return redirect(url_for("notes.view_note", id=note.id))


@notes_bp.route("/api/tag_suggestions")
def tag_suggestions():
    """Return predefined tag suggestions."""
    return jsonify(current_app.config.get("TAG_SUGGESTIONS", []))


@notes_bp.route("/api/categorize", methods=["POST"])
def categorize_text():
    """Return category suggestions for provided text."""
    data = request.get_json() or {}
    text = data.get("text", "")
    cats = current_app.config.get("NOTE_CATEGORIES", [])
    return jsonify(suggest_categories(text, cats))


@notes_bp.route("/<int:note_id>/translation/<string:lang>")
def note_translation(note_id, lang):
    folder = os.path.join(current_app.config["TRANSLATIONS_FOLDER"], "notes")
    path = os.path.join(folder, f"{note_id}.json")
    if not os.path.exists(path):
        abort(404)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        abort(404)
    if lang not in data:
        abort(404)
    return jsonify(data[lang])


@notes_bp.route("/<int:note_id>")
@activated_required
def detail(note_id):
    note = Note.query.get_or_404(note_id)
    note.views += 1
    db.session.commit()

    trans_folder = os.path.join(current_app.config["TRANSLATIONS_FOLDER"], "notes")
    trans_path = os.path.join(trans_folder, f"{note.id}.json")
    translation_langs = []
    if os.path.exists(trans_path):
        try:
            with open(trans_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                translation_langs = list(data.keys())
        except Exception:
            translation_langs = []

    def get_ext(path):
        if path.startswith("http"):
            path = urlparse(path).path
        path = path.split("?")[0]
        return os.path.splitext(path)[1].lower()

    ftype = note.file_type
    if not ftype:
        ext = get_ext(note.original_file_url or note.filename)
        if ext == ".pdf":
            ftype = "pdf"
        elif ext in {".jpg", ".jpeg", ".png", ".webp"}:
            ftype = "image"
        elif ext == ".docx":
            ftype = "docx"
        elif ext == ".pptx":
            ftype = "pptx"
        else:
            ftype = "other"

    return render_template(
        "notes/detalle.html",
        note=note,
        file_type=ftype,
        translation_langs=translation_langs,
    )


@notes_bp.route("/<int:note_id>/embed")
@talisman(
    content_security_policy={**DEFAULT_CSP, "frame-ancestors": "*"},
    frame_options="ALLOWALL",
)
def embed_note(note_id):
    note = Note.query.get_or_404(note_id)
    note.views += 1
    db.session.commit()

    def get_ext(path):
        if path.startswith("http"):
            path = urlparse(path).path
        path = path.split("?")[0]
        return os.path.splitext(path)[1].lower()

    ftype = note.file_type
    if not ftype:
        ext = get_ext(note.original_file_url or note.filename)
        if ext == ".pdf":
            ftype = "pdf"
        elif ext in {".jpg", ".jpeg", ".png", ".webp"}:
            ftype = "image"
        elif ext == ".docx":
            ftype = "docx"
        elif ext == ".pptx":
            ftype = "pptx"
        else:
            ftype = "other"

    return render_template("notes/embed.html", note=note, file_type=ftype)


# Alias endpoint for backward compatibility with templates using
# `notes.view_note` and parameter name `id`.
notes_bp.add_url_rule("/<int:id>", endpoint="view_note", view_func=detail)


@notes_bp.route("/<int:note_id>/comment", methods=["POST"])
def add_comment(note_id):
    note = Note.query.get_or_404(note_id)
    body = request.form["body"]
    if current_user.is_authenticated:
        comment = Comment(body=body, author=current_user, note=note)
        db.session.add(comment)
        note.comments_count += 1
        db.session.commit()
        record_activity("comment_note", comment.id, "note")
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
    else:
        comment = Comment(body=body, note=note, pending=True)
        db.session.add(comment)
        db.session.commit()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"pending": True}), 202
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

    download_url = note.original_file_url or note.filename
    return redirect(download_url)


@notes_bp.route("/<int:note_id>/print", methods=["POST"])
@activated_required
def print_note(note_id):
    """Queue a print request for the given note."""
    note = Note.query.get_or_404(note_id)
    pr = PrintRequest(user_id=current_user.id, note_id=note.id)
    db.session.add(pr)
    db.session.commit()
    flash("Solicitud de impresión en cola", "success")
    return redirect(url_for("notes.view_note", id=note.id))


@notes_bp.route("/delete/<int:note_id>", methods=["POST"], endpoint="delete_note")
@activated_required
def delete_note(note_id):
    """Allow authors to delete their own notes."""
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)

    feed_items = FeedItem.query.filter_by(item_type="apunte", ref_id=note.id).all()
    owner_ids = [fi.owner_id for fi in feed_items]
    FeedItem.query.filter_by(item_type="apunte", ref_id=note.id).delete()
    Credit.query.filter_by(
        user_id=current_user.id, related_id=note.id, reason=CreditReasons.APUNTE_SUBIDO
    ).delete()

    NoteVote.query.filter_by(note_id=note.id).delete()
    Comment.query.filter_by(note_id=note.id).delete()
    PrintRequest.query.filter_by(note_id=note.id).delete()

    if note.filename.startswith("http") and current_app.config.get("CLOUDINARY_URL"):
        public_id = os.path.splitext(note.filename.rsplit("/", 1)[-1])[0]
        try:
            cloudinary.uploader.destroy(
                f"notes/{public_id}", invalidate=True, resource_type="image"
            )
            cloudinary.uploader.destroy(
                f"notes/{public_id}", invalidate=True, resource_type="raw"
            )
        except Exception:
            current_app.logger.exception("Error deleting Cloudinary file")

    db.session.delete(note)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("No se pudo eliminar el apunte por registros relacionados", "danger")
        return redirect(url_for("notes.view_note", id=note.id))

    for uid in owner_ids:
        try:
            remove_item(uid, "apunte", note.id)
        except Exception:
            pass

    flash("Apunte eliminado correctamente", "success")
    return redirect(url_for("notes.list_notes"))


@notes_bp.route("/edit/<int:note_id>", methods=["GET", "POST"], endpoint="edit_note")
@activated_required
def edit_note(note_id):
    """Allow authors to edit title, description, category and tags."""
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        valid_categories = current_app.config.get("NOTE_CATEGORIES", [])
        if valid_categories and category not in valid_categories:
            flash("Categoría inválida", "danger")
            return redirect(url_for("notes.edit_note", note_id=note.id))
        tags = request.form.get("tags", "").strip()
        if not title:
            flash("El título es obligatorio", "danger")
            return redirect(url_for("notes.edit_note", note_id=note.id))
        note.title = title
        note.description = description
        note.category = category
        note.tags = tags
        db.session.commit()
        flash("Apunte actualizado", "success")
        return redirect(url_for("notes.view_note", id=note.id))

    return render_template("notes/edit.html", note=note)


@notes_bp.route("/report/<int:note_id>", methods=["POST"], endpoint="report_note")
@activated_required
def report_note(note_id):
    """Create a report for a note."""
    note = Note.query.get_or_404(note_id)
    if note.user_id == current_user.id:
        abort(403)
    reason = request.form.get("reason", "").strip()
    report = Report(
        user_id=current_user.id,
        description=f"Note {note_id}: {reason}",
    )
    db.session.add(report)
    admin = User.query.filter_by(role="admin").first()
    if admin:
        send_notification(admin.id, f"Nuevo reporte de apunte {note_id}")
    db.session.commit()
    flash("Apunte reportado", "success")
    return redirect(url_for("notes.view_note", id=note.id))
