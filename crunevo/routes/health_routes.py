from flask import Blueprint, jsonify, current_app, make_response
from crunevo.extensions import csrf
import os

try:
    from flask_talisman import Talisman
except Exception:  # pragma: no cover
    Talisman = None

health_bp = Blueprint("health", __name__)


@health_bp.get("/healthz")
def healthz():
    resp = make_response("ok", 200)
    revision = current_app.config.get("GIT_SHA") or os.getenv("GIT_SHA")
    if revision:
        resp.headers["X-App-Revision"] = revision
    return resp


@health_bp.get("/live")
def live():
    return jsonify(status="live"), 200


@health_bp.get("/ready")
def ready():
    return jsonify(status="ready"), 200


csrf.exempt(health_bp)
if Talisman:
    # blueprint will be exempted in app factory
    pass
