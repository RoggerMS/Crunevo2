from flask import Blueprint, render_template, current_app, request

maintenance_bp = Blueprint("maintenance", __name__)


@maintenance_bp.before_app_request
def check_maintenance():
    if not current_app.config.get("MAINTENANCE_MODE"):
        return None
    if request.blueprint and request.blueprint.startswith("admin"):
        return None
    if request.path.startswith("/static") or request.path.startswith("/health"):
        return None
    return render_template("maintenance.html"), 503
