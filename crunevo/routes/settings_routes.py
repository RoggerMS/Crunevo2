from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import User

settings_bp = Blueprint("settings", __name__, url_prefix="/configuracion")


@settings_bp.route("/")
@login_required
@activated_required
def index():
    return render_template("configuracion/index.html")


@settings_bp.route("/personal", methods=["POST"])
@login_required
@activated_required
def update_personal():
    username = request.form.get("username", "").strip()
    about = request.form.get("about", "")
    if username and username != current_user.username:
        if User.query.filter_by(username=username).first():
            return jsonify(success=False, error="Nombre de usuario no disponible"), 400
        current_user.username = username
    current_user.about = about
    db.session.commit()
    return jsonify(success=True)
