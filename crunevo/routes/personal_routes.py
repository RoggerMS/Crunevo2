from flask import Blueprint, render_template
from flask_login import login_required

personal_bp = Blueprint("personal", __name__, url_prefix="/espacio-personal-proto")


@personal_bp.route("/")
@login_required
def space():
    """Prototype personal space using localStorage"""
    return render_template("personal/space.html")
