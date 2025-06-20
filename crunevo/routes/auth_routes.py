from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import login_user, logout_user, current_user
from crunevo.utils.helpers import activated_required
from crunevo.extensions import limiter
from zxcvbn import zxcvbn
from crunevo.utils.audit import record_auth_event
from urllib.parse import urlparse  # ✅ Corrección aquí
import json
import os
import cloudinary.uploader
from werkzeug.utils import secure_filename
from crunevo.extensions import db
from crunevo.models import User
from crunevo.models.user import DEFAULT_AVATAR_URL
from crunevo.utils import spend_credit, record_login
from crunevo.constants import CreditReasons
from sqlalchemy.exc import IntegrityError
from crunevo.routes.onboarding_routes import send_confirmation_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Nombre de usuario ya registrado", "danger")
            return render_template("auth/register.html"), 400
        if len(password) < 12 or zxcvbn(password)["score"] < 2:
            flash("Contraseña débil", "danger")
            return render_template("auth/register.html"), 400
        avatar_url = DEFAULT_AVATAR_URL
        f = request.files.get("avatar_file")
        if f and f.filename:
            cloud_url = current_app.config.get("CLOUDINARY_URL")
            if cloud_url:
                result = cloudinary.uploader.upload(f, resource_type="auto")
                avatar_url = result["secure_url"]
            else:
                filename = secure_filename(f.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                f.save(filepath)
                avatar_url = filepath
        user = User(username=username, email=email, avatar_url=avatar_url)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.warning("IntegrityError: %s", e)
            flash("Usuario o correo ya registrado", "danger")
            return render_template("auth/register.html"), 400
        send_confirmation_email(user)
        return render_template("onboarding/confirm.html")
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes")
def login():
    admin_mode = current_app.config.get("ADMIN_INSTANCE")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            record_auth_event(user, "login_success")
            if not user.activated:
                login_user(user)
                return redirect(url_for("onboarding.pending"))
            login_user(user)
            record_login(user)
            if admin_mode:
                return redirect(url_for("admin.dashboard"))
            next_page = request.args.get("next")
            if not next_page or urlparse(next_page).netloc != "":
                next_page = url_for("feed.index")
            return redirect(next_page)
        record_auth_event(user, "login_fail", extra=json.dumps({"username": username}))
        flash("Credenciales inválidas")
    template = "auth/login_admin.html" if admin_mode else "auth/login.html"
    return render_template(template)


@auth_bp.route("/logout")
@activated_required
def logout():
    user = current_user
    logout_user()
    record_auth_event(user, "logout")
    return redirect(url_for("auth.login"))


@auth_bp.route("/perfil", methods=["GET", "POST"])
@activated_required
def perfil():
    if request.method == "POST":
        current_user.about = request.form.get("about")
        file = request.files.get("avatar_file")
        if file and file.filename:
            cloud_url = current_app.config.get("CLOUDINARY_URL")
            if cloud_url:
                res = cloudinary.uploader.upload(file, resource_type="auto")
                current_user.avatar_url = res["secure_url"]
            else:
                filename = secure_filename(file.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                current_user.avatar_url = filepath
        db.session.commit()
        flash("Perfil actualizado")
    return render_template("auth/perfil.html")


@auth_bp.route("/user/<int:user_id>")
@activated_required
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("perfil_publico.html", user=user)


@auth_bp.route("/agradecer/<int:user_id>", methods=["POST"])
@activated_required
def agradecer(user_id):
    target = User.query.get_or_404(user_id)
    if target.id == current_user.id:
        flash("No puedes agradecerte a ti mismo", "warning")
        return redirect(url_for("auth.public_profile", user_id=user_id))
    try:
        spend_credit(
            current_user, 1, CreditReasons.AGRADECIMIENTO, related_id=target.id
        )
        flash("¡Gracias enviado!")
    except ValueError:
        flash("No tienes créditos suficientes", "danger")
    return redirect(url_for("auth.public_profile", user_id=user_id))
