from flask import Blueprint, jsonify, request

from crunevo.models.post import Post
from crunevo.utils.jwt_utils import jwt_required

feed_api_bp = Blueprint("feed_api", __name__, url_prefix="/api")


@feed_api_bp.route("/feed")
@jwt_required
def get_feed():
    """Return paginated posts as JSON."""
    page = int(request.args.get("page", 1))
    per_page = 10
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    posts = [
        {"id": p.id, "content": p.content, "created_at": p.created_at.isoformat()}
        for p in pagination.items
    ]
    return jsonify({"page": page, "total": pagination.total, "posts": posts})
