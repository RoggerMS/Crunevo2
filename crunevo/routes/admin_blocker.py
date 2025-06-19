from flask import Blueprint, abort

admin_blocker_bp = Blueprint("admin_blocker", __name__, url_prefix="/admin")


@admin_blocker_bp.route("/", defaults={"path": ""})
@admin_blocker_bp.route("/<path:path>")
def block(path):
    abort(404)
