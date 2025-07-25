from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import current_app, request, jsonify, g

from crunevo.models.user import User


def generate_token(user, expires_in: int = 3600) -> str:
    payload = {
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def jwt_required(f):
    """Simple JWT auth decorator."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )
        except jwt.PyJWTError:
            return jsonify({"error": "Invalid token"}), 401
        user = User.query.get(payload.get("user_id"))
        if not user:
            return jsonify({"error": "Invalid token"}), 401
        g.current_user = user
        return f(*args, **kwargs)

    return wrapper
