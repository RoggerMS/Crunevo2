from flask import Blueprint, render_template

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500
