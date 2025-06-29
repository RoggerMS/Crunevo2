from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.saved_content import SavedContent
from crunevo.models.note import Note
from crunevo.models.post import Post

saved_bp = Blueprint("saved", __name__)


@saved_bp.route("/guardados")
@login_required
def list_saved():
    """List all saved content"""
    saved_notes = (
        db.session.query(SavedContent, Note)
        .join(Note, SavedContent.content_id == Note.id)
        .filter(
            SavedContent.user_id == current_user.id, SavedContent.content_type == "note"
        )
        .order_by(SavedContent.saved_at.desc())
        .all()
    )

    saved_posts = (
        db.session.query(SavedContent, Post)
        .join(Post, SavedContent.content_id == Post.id)
        .filter(
            SavedContent.user_id == current_user.id, SavedContent.content_type == "post"
        )
        .order_by(SavedContent.saved_at.desc())
        .all()
    )

    return render_template(
        "saved/list.html", saved_notes=saved_notes, saved_posts=saved_posts
    )


@saved_bp.route("/api/guardar", methods=["POST"])
@login_required
def save_content():
    """Save content for later"""
    data = request.get_json()
    content_type = data.get("content_type")
    content_id = data.get("content_id")

    if content_type not in ["note", "post"]:
        return jsonify({"error": "Tipo de contenido inválido"}), 400

    # Check if already saved
    existing = SavedContent.query.filter_by(
        user_id=current_user.id, content_type=content_type, content_id=content_id
    ).first()

    if existing:
        # Remove from saved
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"success": True, "saved": False})
    else:
        # Add to saved
        saved = SavedContent(
            user_id=current_user.id, content_type=content_type, content_id=content_id
        )
        db.session.add(saved)
        db.session.commit()
        return jsonify({"success": True, "saved": True})


@saved_bp.route("/api/guardar/estado", methods=["POST"])
@login_required
def check_saved_status():
    """Check if content is saved"""
    data = request.get_json()
    content_type = data.get("content_type")
    content_id = data.get("content_id")

    saved = SavedContent.query.filter_by(
        user_id=current_user.id, content_type=content_type, content_id=content_id
    ).first()

    return jsonify({"saved": saved is not None})
