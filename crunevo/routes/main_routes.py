from flask import Blueprint, render_template
from crunevo.routes.feed_routes import feed_home

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return feed_home()


@main_bp.route("/terms")
def terms():
    return render_template("terms.html")
