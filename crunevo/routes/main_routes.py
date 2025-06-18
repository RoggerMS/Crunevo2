from flask import Blueprint
from crunevo.routes.feed_routes import index as feed_index

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return feed_index()
