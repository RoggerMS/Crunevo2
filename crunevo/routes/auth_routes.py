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
from crunevo.utils.audit import record_auth_event
from urllib.parse import urlparse  # ✅ Corrección aquí
import json
import os
import cloudinary.uploader
from werkzeug.utils import secure_filename
from crunevo.extensions import db
from crunevo.models import User, Note
from crunevo.utils import spend_credit, record_login, send_notification
from crunevo.constants import CreditReasons

IS_ADMIN = os.environ.get("ADMIN_INSTANCE") == "1"

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@auth_bp.route("/", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes")
def login():
    admin_mode = current_app.config.get("ADMIN_INSTANCE")
    template = "auth/login_admin.html" if admin_mode else "auth/login.html"
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if admin_mode and user.role not in ("admin", "moderator"):
                record_auth_event(
                    user,
                    "login_fail",
                    extra=json.dumps({"username": username, "reason": "role"}),
                )
                flash(
                    "Acceso restringido a administradores y moderadores",
                    "danger",
                )
                return render_template(template), 403
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
                next_page = url_for("feed.feed_home")
            return redirect(next_page)
        record_auth_event(user, "login_fail", extra=json.dumps({"username": username}))
        flash("Credenciales inválidas")
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
    tab = request.args.get("tab")
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
    from crunevo.models import SavedPost, Post
    from crunevo.constants import ACHIEVEMENT_CATEGORIES

    saved = SavedPost.query.filter_by(user_id=current_user.id).all()
    posts = [Post.query.get(sp.post_id) for sp in saved if Post.query.get(sp.post_id)]

    ach_type = request.args.get("tipo")
    achievements = current_user.achievements
    if ach_type:
        achievements = [
            a
            for a in achievements
            if ACHIEVEMENT_CATEGORIES.get(a.badge_code) == ach_type
        ]

    missions = None
    if tab == "misiones":
        from crunevo.routes.missions_routes import compute_mission_states

        missions = compute_mission_states(current_user)

    return render_template(
        "auth/perfil.html",
        saved_posts=posts,
        achievements=achievements,
        ach_type=ach_type,
        tab=tab,
        missions=missions,
    )


@auth_bp.route("/user/<int:user_id>")
@activated_required
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("perfil_publico.html", user=user)


@auth_bp.route("/perfil/<username>")
@activated_required
def profile_by_username(username: str):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("perfil_publico.html", user=user)


@auth_bp.route("/perfil/<username>/apuntes")
@activated_required
def notes_by_username(username: str):
    """Display all notes from a user by username."""
    user = User.query.filter_by(username=username).first_or_404()
    notes = Note.query.filter_by(user_id=user.id).order_by(Note.created_at.desc()).all()
    return render_template("perfil_notas.html", user=user, notes=notes)


@auth_bp.route("/agradecer/<int:user_id>", methods=["POST"])
@activated_required
def agradecer(user_id):
    target = User.query.get_or_404(user_id)
    if target.id == current_user.id:
        flash("No puedes agradecerte a ti mismo", "warning")
        return redirect(url_for("auth.profile_by_username", username=target.username))
    try:
        spend_credit(
            current_user, 1, CreditReasons.AGRADECIMIENTO, related_id=target.id
        )
        send_notification(
            target.id, f"{current_user.username} te ha agradecido con 1 crédito."
        )
        flash("¡Gracias enviado!")
    except ValueError:
        flash("No tienes créditos suficientes", "danger")
    return redirect(url_for("auth.profile_by_username", username=target.username))
