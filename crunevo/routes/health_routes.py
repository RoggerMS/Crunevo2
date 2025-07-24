from flask import Blueprint
from crunevo.extensions import talisman

health_bp = Blueprint("health", __name__)


@health_bp.route("/healthz")
@talisman(force_https=False)
def healthz():
    return "ok"


@health_bp.route("/ping")
def ping():
    return "pong"
