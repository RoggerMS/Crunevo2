from flask import Blueprint, render_template

static_bp = Blueprint("static_pages", __name__)


@static_bp.route("/cookies")
def cookies():
    return render_template("static/cookies.html")
