from flask import Blueprint, render_template

errors_bp = Blueprint("errors", __name__)


@errors_bp.app_errorhandler(500)
def internal_error(error):
    return render_template("errors/500.html"), 500


@errors_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@errors_bp.app_errorhandler(429)
def too_many_requests(error):
    return render_template("errors/429.html"), 429
