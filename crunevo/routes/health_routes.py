from flask import Blueprint, current_app
from sqlalchemy import text
from crunevo.extensions import talisman, db

health_bp = Blueprint("health", __name__)


@health_bp.route("/healthz")
@talisman(force_https=False)
def healthz():
    try:
        db.session.execute(text("SELECT 1"))
        return "ok", 200
    except Exception as e:  # pragma: no cover - avoid failing tests on DB down
        current_app.logger.error(f"Health check failed: {e}")
        return "error", 500


@health_bp.route("/ping")
def ping():
    return "pong"
