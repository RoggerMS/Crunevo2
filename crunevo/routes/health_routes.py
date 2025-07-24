from flask import Blueprint, current_app
from sqlalchemy import text

from crunevo.extensions import db, talisman

health_bp = Blueprint("health", __name__)


@health_bp.route("/healthz")
@talisman(force_https=False)
def healthz():
    try:
        db.session.execute(text("SELECT 1"))
        return "ok", 200
    except Exception:
        current_app.logger.exception("Health check failed")
        return "error", 500


@health_bp.route("/ping")
def ping():
    return "pong"
