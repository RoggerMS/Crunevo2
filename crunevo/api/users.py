from flask import Blueprint, jsonify, request, g

from crunevo.models.user import User
from crunevo.utils.jwt_utils import generate_token, jwt_required

users_api_bp = Blueprint("users_api", __name__, url_prefix="/api")


@users_api_bp.route("/token", methods=["POST"])
def issue_token():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"token": generate_token(user)})


@users_api_bp.route("/user")
@jwt_required
def current_user_info():
    user = g.current_user
    return jsonify({"id": user.id, "username": user.username})
