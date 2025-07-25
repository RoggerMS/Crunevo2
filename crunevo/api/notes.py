from flask import Blueprint, jsonify, request

from crunevo.models.note import Note
from crunevo.utils.jwt_utils import jwt_required

notes_api_bp = Blueprint("notes_api", __name__, url_prefix="/api")


@notes_api_bp.route("/notes")
@jwt_required
def list_notes():
    page = int(request.args.get("page", 1))
    per_page = 10
    pagination = Note.query.order_by(Note.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    notes = [
        {"id": n.id, "title": n.title, "created_at": n.created_at.isoformat()}
        for n in pagination.items
    ]
    return jsonify({"page": page, "total": pagination.total, "notes": notes})
