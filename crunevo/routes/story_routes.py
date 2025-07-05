import os
from datetime import datetime, timedelta
import cloudinary.uploader
from werkzeug.utils import secure_filename
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import current_user
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import Story


stories_bp = Blueprint("stories", __name__, url_prefix="/stories")


@stories_bp.route("/", methods=["GET"], endpoint="list_stories")
@activated_required
def list_stories():
    active = Story.query.filter(Story.expires_at > datetime.utcnow()).all()
    return render_template("stories/list.html", stories=active)


@stories_bp.route("/upload", methods=["GET", "POST"], endpoint="upload_story")
@activated_required
def upload_story():
    if request.method == "POST":
        image = request.files.get("image")
        if not image or not image.filename:
            flash("Selecciona una imagen", "danger")
            return redirect(url_for("stories.upload_story"))
        cloud_url = current_app.config.get("CLOUDINARY_URL")
        try:
            if cloud_url:
                res = cloudinary.uploader.upload(image, resource_type="auto")
                url = res["secure_url"]
            else:
                filename = secure_filename(image.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                path = os.path.join(upload_folder, filename)
                image.save(path)
                url = path
        except Exception:
            current_app.logger.exception("Error uploading story")
            flash("No se pudo subir la historia", "danger")
            return redirect(url_for("stories.upload_story"))

        expires = datetime.utcnow() + timedelta(hours=24)
        story = Story(user_id=current_user.id, image_url=url, expires_at=expires)
        db.session.add(story)
        db.session.commit()
        flash("Historia publicada", "success")
        return redirect(url_for("stories.list_stories"))

    return render_template("stories/upload.html")
