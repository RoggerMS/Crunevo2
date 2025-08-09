from flask import Blueprint
from crunevo.extensions import talisman

health_bp = Blueprint("health", __name__)


@health_bp.get("/healthz")
@talisman(force_https=False)
def healthz():
    return "ok", 200


@health_bp.get("/health")
@talisman(force_https=False)
def health():
    return "ok", 200


@health_bp.route("/ping")
def ping():
    return "pong"
