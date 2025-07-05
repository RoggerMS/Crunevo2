from flask import Blueprint, jsonify, request, g
from flask_login import login_required, current_user
from flask_limiter.util import get_remote_address

from crunevo.extensions import db, limiter
from crunevo.models import Post, Note, APIKey


developer_bp = Blueprint("developer_api", __name__, url_prefix="/api")


def api_key_func():
    return (
        g.get("api_key")
        or request.headers.get("X-API-Key")
        or request.args.get("api_key")
        or get_remote_address()
    )


def api_key_required(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if not key:
            return jsonify({"error": "API key required"}), 401
        api_key = APIKey.query.filter_by(key=key).first()
        if not api_key:
            return jsonify({"error": "Invalid API key"}), 401
        g.api_key = key
        g.api_user = api_key.user
        return f(*args, **kwargs)

    return wrapper


@developer_bp.route("/recent-posts")
@limiter.limit("30 per minute", key_func=api_key_func)
@api_key_required
def recent_posts():
    posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    return jsonify(
        [
            {"id": p.id, "content": p.content, "created_at": p.created_at.isoformat()}
            for p in posts
        ]
    )


@developer_bp.route("/popular-notes")
@limiter.limit("30 per minute", key_func=api_key_func)
@api_key_required
def popular_notes():
    notes = Note.query.order_by(Note.likes.desc()).limit(10).all()
    return jsonify([{"id": n.id, "title": n.title, "likes": n.likes} for n in notes])


@developer_bp.route("/generate-key", methods=["POST"])
@login_required
def generate_key():
    api_key = APIKey.query.filter_by(user_id=current_user.id).first()
    if not api_key:
        api_key = APIKey(user_id=current_user.id)
        db.session.add(api_key)
        db.session.commit()
    return jsonify({"api_key": api_key.key})
