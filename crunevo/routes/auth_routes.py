from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    jsonify,
    session,
)
from flask_login import login_user, logout_user, current_user, login_required
from crunevo.utils.helpers import activated_required
from crunevo.cache import login_attempts
from crunevo.utils.audit import record_auth_event
from urllib.parse import urlparse  # ✅ Corrección aquí
import json
import os
import cloudinary.uploader
from werkzeug.utils import secure_filename
from crunevo.extensions import db, csrf
from crunevo.models import User, Note, TwoFactorToken
from crunevo.utils import (
    spend_credit,
    record_login,
    send_notification,
    add_credit,
    record_activity,
)
from crunevo.constants import CreditReasons
from crunevo.utils.login_streak import streak_reward
from datetime import date, datetime, timedelta
from crunevo.models import DeviceClaim
import pyotp
import secrets

IS_ADMIN = os.environ.get("ADMIN_INSTANCE") == "1"

auth_bp = Blueprint("auth", __name__)


def _has_2fa_table() -> bool:
    """Return True if the TwoFactorToken table exists."""
    from sqlalchemy import inspect

    return inspect(db.engine).has_table("two_factor_token")


@auth_bp.route("/register")
def redirect_register():
    return redirect(url_for("onboarding.register"))


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
            record = None
            if _has_2fa_table():
                try:
                    record = user.two_factor
                except Exception:
                    db.session.rollback()
            if record and record.confirmed_at:
                session["2fa_user_id"] = user.id
                session["next"] = request.args.get("next")
                return redirect(url_for("auth.verify_token"))
            login_user(user)
            record_login(user)
            record_activity("login")
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


@auth_bp.route("/login/verify", methods=["GET", "POST"])
def verify_token():
    user_id = session.get("2fa_user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    user = User.query.get(user_id)
    if not _has_2fa_table():
        return redirect(url_for("auth.login"))
    record = None
    try:
        record = user.two_factor
    except Exception:
        db.session.rollback()
    if not record or not record.confirmed_at:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        code = request.form.get("code")
        totp = pyotp.TOTP(record.secret)
        valid = totp.verify(code)
        if not valid and record.backup_codes:
            codes = record.backup_codes.split(",")
            if code in codes:
                codes.remove(code)
                record.backup_codes = ",".join(codes)
                valid = True
        if valid:
            login_user(user)
            record_login(user)
            record_activity("login")
            session.pop("2fa_user_id", None)
            next_page = session.pop("next", None)
            admin_mode = current_app.config.get("ADMIN_INSTANCE")
            if admin_mode:
                return redirect(url_for("admin.dashboard"))
            if not next_page or urlparse(next_page).netloc != "":
                next_page = url_for("feed.feed_home")
            db.session.commit()
            return redirect(next_page)
        flash("Código inválido", "danger")
    return render_template("auth/two_factor_verify.html")


@auth_bp.route("/logout")
@activated_required
def logout():
    user = current_user._get_current_object()
    logout_user()
    record_auth_event(user, "logout")
    return redirect(url_for("auth.login"))


def _generate_backup_codes(n=5):
    return [secrets.token_hex(4) for _ in range(n)]


@auth_bp.route("/2fa/setup", methods=["GET", "POST"])
@login_required
def setup_2fa():
    if not _has_2fa_table():
        return redirect(url_for("auth.perfil"))
    record = TwoFactorToken.query.filter_by(user_id=current_user.id).first()
    if request.method == "POST":
        if not record:
            return redirect(url_for("auth.setup_2fa"))
        code = request.form.get("code")
        totp = pyotp.TOTP(record.secret)
        if totp.verify(code):
            record.confirmed_at = datetime.utcnow()
            record.backup_codes = ",".join(_generate_backup_codes())
            db.session.commit()
            flash("Autenticación de dos factores activada")
            return redirect(url_for("auth.perfil"))
        flash("Código inválido", "danger")
    else:
        if not record:
            secret = pyotp.random_base32()
            record = TwoFactorToken(user_id=current_user.id, secret=secret)
            db.session.add(record)
            db.session.commit()
    qr_url = pyotp.totp.TOTP(record.secret).provisioning_uri(
        name=current_user.email, issuer_name="Crunevo"
    )
    codes = record.backup_codes.split(",") if record.backup_codes else []
    return render_template(
        "auth/enable_2fa.html",
        secret=record.secret,
        qr_url=qr_url,
        confirmed=bool(record.confirmed_at),
        codes=codes,
    )


@auth_bp.route("/2fa/backup", methods=["POST"])
@login_required
def regen_backup_codes():
    if not _has_2fa_table():
        return redirect(url_for("auth.setup_2fa"))
    record = current_user.two_factor
    if not record or not record.confirmed_at:
        return redirect(url_for("auth.setup_2fa"))
    record.backup_codes = ",".join(_generate_backup_codes())
    db.session.commit()
    return jsonify(codes=record.backup_codes.split(","))


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
    from crunevo.models import (
        SavedPost,
        Post,
        ClubMember,
        UserMission,
        Note,
        PostComment,
        Comment,
        Purchase,
    )
    from crunevo.constants import ACHIEVEMENT_DETAILS, ACHIEVEMENT_CATEGORIES

    saved = SavedPost.query.filter_by(user_id=current_user.id).all()
    posts = [Post.query.get(sp.post_id) for sp in saved if Post.query.get(sp.post_id)]

    # Quick counts for profile stats
    user_clubs = [
        cm.club for cm in ClubMember.query.filter_by(user_id=current_user.id).all()
    ]
    completed_missions_count = UserMission.query.filter_by(
        user_id=current_user.id
    ).count()

    # Academic level and participation metrics
    user_level = min(
        10, (current_user.points or 0) // 100 + current_user.verification_level
    )
    activity_total = (
        len(current_user.post_comments or [])
        + len(current_user.posts or [])
        + len(current_user.notes or [])
    )
    participation_percentage = (
        min(100, int((activity_total / 30) * 100)) if activity_total else 0
    )

    # Build recent activity feed
    recent_activities = []
    for post in (
        Post.query.filter_by(author_id=current_user.id)
        .order_by(Post.created_at.desc())
        .limit(5)
    ):
        recent_activities.append(
            {
                "timestamp": post.created_at,
                "description": "Publicaste en el feed",
                "icon": "pencil-square",
                "type_color": "primary",
            }
        )

    for note in (
        Note.query.filter_by(user_id=current_user.id)
        .order_by(Note.created_at.desc())
        .limit(5)
    ):
        recent_activities.append(
            {
                "timestamp": note.created_at,
                "description": f"Subiste un apunte llamado {note.title}",
                "icon": "journal-text",
                "type_color": "success",
            }
        )

    for comment in (
        Comment.query.filter_by(user_id=current_user.id)
        .order_by(Comment.created_at.desc())
        .limit(5)
    ):
        recent_activities.append(
            {
                "timestamp": comment.created_at,
                "description": "Comentaste en un apunte",
                "icon": "chat-left-text",
                "type_color": "info",
            }
        )

    for pcom in (
        PostComment.query.filter_by(author_id=current_user.id)
        .order_by(PostComment.timestamp.desc())
        .limit(5)
    ):
        recent_activities.append(
            {
                "timestamp": pcom.timestamp,
                "description": "Comentaste en una publicación",
                "icon": "chat-left-text",
                "type_color": "info",
            }
        )

    for um in (
        UserMission.query.filter_by(user_id=current_user.id)
        .order_by(UserMission.completed_at.desc())
        .limit(5)
    ):
        if um.mission:
            desc = f"Completaste la misión {um.mission.description}"
        else:
            desc = "Completaste una misión"
        recent_activities.append(
            {
                "timestamp": um.completed_at,
                "description": desc,
                "icon": "trophy",
                "type_color": "warning",
            }
        )

    recent_activities.sort(key=lambda a: a["timestamp"], reverse=True)
    recent_activities = recent_activities[:5]

    ach_type = request.args.get("tipo")
    all_user_achievements = current_user.achievements
    achievements = all_user_achievements
    if ach_type:
        achievements = [
            a
            for a in all_user_achievements
            if ACHIEVEMENT_CATEGORIES.get(a.badge_code) == ach_type
        ]

    total_achievements = len(ACHIEVEMENT_DETAILS)
    user_achievements_map = {a.badge_code: a for a in all_user_achievements}

    unlocked_achievements = []
    locked_achievements = []
    for code, info in ACHIEVEMENT_DETAILS.items():
        if code in user_achievements_map:
            unlocked_achievements.append((code, info))
        else:
            locked_achievements.append((code, info))

    misiones = None
    progresos = None
    group_missions = None
    group_progress = None
    referidos = None
    total_referidos = 0
    referidos_completados = 0
    enlace_referido = None
    creditos_referidos = 0
    purchases = None
    if tab == "misiones":
        from crunevo.routes.missions_routes import (
            compute_mission_states,
            compute_group_mission_states,
        )
        from crunevo.models import Mission, GroupMission

        misiones = Mission.query.all()
        progresos = compute_mission_states(current_user)
        group_missions = (
            GroupMission.query.join(GroupMission.participants)
            .filter_by(user_id=current_user.id)
            .all()
        )
        group_progress = compute_group_mission_states(current_user)
    elif tab == "compras":
        purchases = (
            Purchase.query.filter_by(user_id=current_user.id)
            .order_by(Purchase.timestamp.desc())
            .all()
        )
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
        group_missions=group_missions,
        group_progress=group_progress,
        referidos=referidos,
        total_referidos=total_referidos,
        referidos_completados=referidos_completados,
        enlace_referido=enlace_referido,
        creditos_referidos=creditos_referidos,
        user_level=user_level,
        user_clubs=user_clubs,
        completed_missions_count=completed_missions_count,
        participation_percentage=participation_percentage,
        recent_activities=recent_activities,
        purchases=purchases,
        total_achievements=total_achievements,
        user_achievements_map=user_achievements_map,
        user_achievements=all_user_achievements,
        unlocked_achievements=unlocked_achievements,
        locked_achievements=locked_achievements,
    )


@auth_bp.route("/perfil/avatar", methods=["POST"])
@activated_required
def update_avatar():
    """Handle avatar update with optional Cloudinary upload."""
    file = request.files.get("avatar")
    if not file or not file.filename:
        flash("No se seleccion\u00f3 ninguna imagen", "danger")
        return redirect(url_for("auth.perfil"))

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
    flash("Avatar actualizado")
    return redirect(url_for("auth.perfil"))


@auth_bp.route("/perfil/banner", methods=["POST"])
@activated_required
def update_banner():
    file = request.files.get("banner")
    if not file or not file.filename:
        flash("No se seleccionó ninguna imagen", "danger")
        return redirect(url_for("auth.perfil"))

    res = cloudinary.uploader.upload(file, resource_type="image")
    current_user.banner_url = res["secure_url"]
    db.session.commit()
    flash("Banner actualizado")
    return redirect(url_for("auth.perfil"))


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


@auth_bp.route("/resend-confirmation", methods=["POST"])
@login_required
def resend_confirmation():
    data = request.get_json()
    new_email = data.get("email") if data else None

    if not new_email or "@" not in new_email:
        return jsonify(success=False, error="Correo no válido."), 400

    if User.query.filter_by(email=new_email).first():
        return jsonify(success=False, error="Ese correo ya está en uso."), 400

    current_user.email = new_email
    current_user.activated = False
    db.session.commit()

    from crunevo.routes.onboarding_routes import send_confirmation_email

    send_confirmation_email(current_user)
    return jsonify(success=True)


csrf.exempt(resend_confirmation)


@auth_bp.route("/perfil/eliminar-cuenta", methods=["POST"])
@activated_required
def delete_account():
    from flask_login import logout_user
    from crunevo.models import (
        LoginStreak,
    )

    for post in current_user.posts:
        db.session.delete(post)
    for note in current_user.notes:
        db.session.delete(note)
    for comment in current_user.comments:
        db.session.delete(comment)
    for pcomment in current_user.post_comments:
        db.session.delete(pcomment)
    for notif in current_user.notifications.all():
        db.session.delete(notif)

    streak = LoginStreak.query.filter_by(user_id=current_user.id).first()
    if streak:
        db.session.delete(streak)

    current_user.activated = False
    current_user.password_hash = ""
    current_user.chat_enabled = False
    db.session.commit()
    logout_user()
    return redirect(url_for("auth.account_deleted"))


@auth_bp.route("/cuenta-eliminada")
def account_deleted():
    return render_template("auth/account_deleted.html")


@auth_bp.route("/api/user")
@login_required
def api_user():
    """Return basic data for the currently logged in user."""
    return jsonify(
        {
            "activated": current_user.activated,
            "username": current_user.username,
            "verification_level": current_user.verification_level,
        }
    )
