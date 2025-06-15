from flask import Blueprint, current_app
from sqlalchemy import text
from crunevo.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/healthz")
def healthz():
    try:
        db.session.execute(text("SELECT 1"))
        return "ok"
    except Exception as e:
        current_app.logger.error("Healthz DB error: %s", e)
        return "error", 500


@health_bp.route("/ping")
def ping():
    return "pong"
