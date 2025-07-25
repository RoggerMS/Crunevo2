from flask import Blueprint
from crunevo.extensions import csrf

feed_bp = Blueprint("feed", __name__, url_prefix="/feed")
csrf.exempt(feed_bp)

# Import views and api to register routes
from . import views, api  # noqa: F401,E402
