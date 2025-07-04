from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import User, VerificationRequest

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
    username = request.form.get("username")
    about = request.form.get("about")
    changed = False
    if username is not None:
        username = username.strip()
        if username and username != current_user.username:
            if User.query.filter_by(username=username).first():
                return (
                    jsonify(success=False, error="Nombre de usuario no disponible"),
                    400,
                )
            current_user.username = username
            changed = True
    if about is not None:
        current_user.about = about
    db.session.commit()
    return jsonify(success=True, changed_username=changed)


@settings_bp.route("/password", methods=["POST"])
@login_required
@activated_required
def update_password():
    current = request.form.get("current_password")
    new_pw = request.form.get("new_password")
    confirm = request.form.get("confirm_new")
    if not current_user.check_password(current):
        return (
            jsonify(success=False, error="Contraseña actual incorrecta"),
            400,
        )
    if not new_pw or new_pw != confirm:
        return (
            jsonify(success=False, error="Las contraseñas no coinciden"),
            400,
        )
    current_user.set_password(new_pw)
    db.session.commit()
    return jsonify(success=True)


@settings_bp.route("/verificacion", methods=["POST"])
@login_required
@activated_required
def submit_verification():
    info = request.form.get("info", "").strip()
    if not info:
        return jsonify(success=False, error="Debes incluir la información"), 400
    existing = VerificationRequest.query.filter_by(
        user_id=current_user.id, status="pending"
    ).first()
    if existing:
        return jsonify(success=False, error="Solicitud ya enviada"), 400
    vr = VerificationRequest(user_id=current_user.id, info=info)
    current_user.verification_level = 1
    db.session.add(vr)
    db.session.commit()
    return jsonify(success=True)


@settings_bp.route("/api/check_username")
@login_required
@activated_required
def api_check_username():
    username = request.args.get("username", "").strip()
    if not username or username == current_user.username:
        return jsonify(available=True)
    exists = User.query.filter_by(username=username).first() is not None
    return jsonify(available=not exists)
