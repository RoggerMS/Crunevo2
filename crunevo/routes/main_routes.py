from flask import Blueprint

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return "CRUNEVO est\u00e1 en l\u00ednea \ud83d\ude80", 200
