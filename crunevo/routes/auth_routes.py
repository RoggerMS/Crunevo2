from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    jsonify,
)
from flask_login import login_user, logout_user, current_user
from crunevo.utils.helpers import activated_required
from crunevo.cache import login_attempts
from crunevo.utils.audit import record_auth_event
from urllib.parse import urlparse  # ✅ Corrección aquí
import json
import os
import cloudinary.uploader
from werkzeug.utils import secure_filename
from crunevo.extensions import db
from crunevo.models import User, Note
from crunevo.utils import spend_credit, record_login, send_notification, add_credit
from crunevo.constants import CreditReasons
from crunevo.utils.login_streak import streak_reward
from datetime import date, datetime, timedelta
from crunevo.models import DeviceClaim

IS_ADMIN = os.environ.get("ADMIN_INSTANCE") == "1"

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    admin_mode = current_app.config.get("ADMIN_INSTANCE")
    template = "auth/login_admin.html" if admin_mode else "auth/login.html"
    error = None
    wait = 0
    if request.method == "POST":
        username = request.form["username"]
        if login_attempts.is_blocked(username):
            wait = login_attempts.get_remaining(username)
            error = (
                "⚠️ Has excedido el número de intentos. Intenta de nuevo en 15 minutos."
            )
            return render_template(template, error=error, wait=wait)

        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_attempts.reset(username)
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
        login_attempts.record_fail(username)
        record_auth_event(user, "login_fail", extra=json.dumps({"username": username}))
        flash("Credenciales inválidas")
    return render_template(template, error=error, wait=wait)


@auth_bp.route("/logout")
@activated_required
def logout():
    user = current_user._get_current_object()
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

    misiones = None
    progresos = None
    referidos = None
    total_referidos = 0
    referidos_completados = 0
    enlace_referido = None
    creditos_referidos = 0
    user_level = current_user.verification_level * 2
    if tab == "misiones":
        from crunevo.routes.missions_routes import compute_mission_states
        from crunevo.models import Mission

        misiones = Mission.query.all()
        progresos = compute_mission_states(current_user)
    elif tab == "referidos":
        from crunevo.models import Referral
        from crunevo.models import Credit
        from crunevo.constants import CreditReasons
        from sqlalchemy import func
        from sqlalchemy.exc import ProgrammingError, OperationalError

        try:
            referidos = Referral.query.filter_by(invitador_id=current_user.id).all()
            total_referidos = len(referidos)
            referidos_completados = sum(1 for r in referidos if r.completado)
            creditos_referidos = (
                db.session.query(func.coalesce(func.sum(Credit.amount), 0))
                .filter_by(user_id=current_user.id, reason=CreditReasons.REFERIDO)
                .scalar()
                or 0
            )
        except (ProgrammingError, OperationalError):
            db.session.rollback()
        enlace_referido = url_for(
            "onboarding.register", ref=current_user.username, _external=True
        )

    return render_template(
        "auth/perfil.html",
        user=current_user,
        saved_posts=posts,
        achievements=achievements,
        ach_type=ach_type,
        tab=tab,
        misiones=misiones,
        progresos=progresos,
        referidos=referidos,
        total_referidos=total_referidos,
        referidos_completados=referidos_completados,
        enlace_referido=enlace_referido,
        creditos_referidos=creditos_referidos,
        user_level=user_level,
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
            target.id, f"{current_user.username} te ha agradecido con 1 crolar."
        )
        flash("¡Gracias enviado!")
    except ValueError:
        flash("No tienes crolars suficientes", "danger")
    return redirect(url_for("auth.profile_by_username", username=target.username))


@auth_bp.route("/api/reclamar-racha", methods=["POST"])
@activated_required
def reclamar_racha():
    today = date.today()
    streak = current_user.login_streak
    if not streak or streak.last_login != today:
        return jsonify({"success": False, "message": "No has iniciado sesión hoy"}), 400
    if streak.claimed_today == today:
        return jsonify({"success": False, "message": "Ya reclamaste hoy"}), 400

    token = request.headers.get("X-Device-Token")
    code = f"racha_dia_{streak.current_day}"
    if token:
        limit = datetime.utcnow() - timedelta(hours=24)
        exists = (
            DeviceClaim.query.filter_by(device_token=token, mission_code=code)
            .filter(DeviceClaim.timestamp >= limit)
            .first()
        )
        if exists:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Este dispositivo ya canjeó esta recompensa recientemente.",
                    }
                ),
                400,
            )

    reward = streak_reward(streak.current_day)
    add_credit(current_user, reward, CreditReasons.RACHA_LOGIN)
    streak.claimed_today = today
    if token:
        db.session.add(
            DeviceClaim(
                device_token=token,
                mission_code=code,
                user_id=current_user.id,
            )
        )
    db.session.commit()
    return jsonify(
        {
            "success": True,
            "credits": reward,
            "day": streak.current_day,
            "balance": current_user.credits,
        }
    )
