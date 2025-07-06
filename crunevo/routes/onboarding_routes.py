from datetime import datetime, timedelta
import os
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
)
from flask_login import login_user, current_user, login_required
import secrets

import cloudinary.uploader
from werkzeug.utils import secure_filename

from crunevo.extensions import db, limiter, csrf
from flask_limiter.util import get_remote_address
from crunevo.models import User, EmailToken
from crunevo.models.user import DEFAULT_AVATAR_URL
from crunevo.utils.mailer import send_email
from crunevo.utils.audit import record_auth_event
import re
from sqlalchemy.exc import IntegrityError

bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")
onboarding_bp = bp


def generate_token():
    return secrets.token_urlsafe(32)


def send_confirmation_email(user):
    token = generate_token()
    db.session.add(EmailToken(token=token, email=user.email, user_id=user.id))
    db.session.commit()
    confirm_url = url_for("onboarding.confirm", token=token, _external=True)
    html = render_template("emails/confirm.html", confirm_url=confirm_url)
    success, error = send_email(user.email, "¡Confirma tu cuenta en CRUNEVO!", html)
    return success, error


def _user_key():
    return current_user.get_id() or get_remote_address()


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("15 per hour", deduct_when=lambda r: request.method == "POST")
def register():
    if request.method == "POST":
        email = request.form["email"]
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Ingresa un correo v\u00e1lido", "danger")
            return render_template("onboarding/register.html"), 400
        password = request.form["password"]
        if (
            len(password) < 6
            or not any(c.isalpha() for c in password)
            or not any(c.isdigit() for c in password)
        ):
            flash(
                "Tu contraseña debe tener al menos 6 caracteres, incluyendo letras y números.",
                "danger",
            )
            return render_template("onboarding/register.html"), 400
        user = User(username=email, email=email)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.warning("IntegrityError: %s", e)
            flash("Usuario o correo ya registrado", "danger")
            return render_template("onboarding/register.html"), 400

        # vincular referido si viene el código en la URL
        ref = request.args.get("ref")
        if ref:
            from crunevo.models import Referral
            from sqlalchemy.exc import ProgrammingError, OperationalError

            referidor = User.query.filter_by(username=ref).first()
            if referidor:
                codigo = f"{referidor.username}-{user.username}"
                try:
                    if not Referral.query.filter_by(code=codigo).first():
                        db.session.add(
                            Referral(
                                code=codigo,
                                invitador_id=referidor.id,
                                invitado_id=user.id,
                            )
                        )
                        db.session.commit()
                except (ProgrammingError, OperationalError):
                    db.session.rollback()
    success, error = send_confirmation_email(user)
    if not success:
        flash(
            "No se pudo enviar el correo de confirmación. Inténtalo más tarde.",
            "danger",
        )
        if error:
            flash(error, "danger")
    return redirect(url_for("onboarding.confirm_sent"))


@bp.route("/confirm")
def confirm_sent():
    """Display page instructing the user to check their email."""
    return render_template("onboarding/confirm.html")


@bp.route("/confirm/<token>")
def confirm(token):
    record = EmailToken.query.filter_by(token=token).first_or_404()
    exp_h = current_app.config["ONBOARDING_TOKEN_EXP_H"]
    if record.consumed_at or datetime.utcnow() - record.created_at > timedelta(
        hours=exp_h
    ):
        flash("Token inválido o expirado")
        return redirect(url_for("onboarding.register"))
    record.consumed_at = datetime.utcnow()
    record.user.activated = True
    from crunevo.models import Referral, Credit
    from crunevo.utils.credits import add_credit
    from crunevo.constants import CreditReasons, AchievementCodes
    from crunevo.utils.achievements import unlock_achievement
    from sqlalchemy.exc import ProgrammingError, OperationalError

    ref = None
    try:
        ref = Referral.query.filter_by(invitado_id=record.user.id).first()
    except (ProgrammingError, OperationalError):
        db.session.rollback()
    if ref and not ref.completado:
        ref.completado = True
        existing = Credit.query.filter_by(
            user_id=ref.invitador_id,
            reason=CreditReasons.REFERIDO,
            related_id=ref.id,
        ).first()
        if not existing:
            add_credit(ref.invitador, 100, CreditReasons.REFERIDO, related_id=ref.id)
            add_credit(record.user, 50, CreditReasons.REFERIDO, related_id=ref.id)
        total_done = Referral.query.filter_by(
            invitador_id=ref.invitador_id, completado=True
        ).count()
        if total_done >= 10:
            unlock_achievement(ref.invitador, AchievementCodes.EMBAJADOR_CRUNEVO)
    db.session.commit()
    db.session.refresh(record.user)
    record_auth_event(record.user, "confirm_email")
    # Force login to ensure session updates even if a different user
    # was previously authenticated
    login_user(record.user, fresh=True, force=True)
    # Remove stale flash messages from previous requests
    session.pop("_flashes", None)
    flash("¡Correo verificado! Bienvenido a CRUNEVO", "success")
    user = record.user
    if user.username == user.email or user.avatar_url == DEFAULT_AVATAR_URL:
        return redirect(url_for("onboarding.finish"))
    return redirect(url_for("feed.feed_home"))


@bp.route("/finish", methods=["GET", "POST"])
@login_required
def finish():
    if request.method == "POST":
        alias = request.form.get("alias")
        if alias:
            current_user.username = alias
        avatar_url = request.form.get("avatar_url")
        avatar_file = request.files.get("avatar_file")
        if avatar_file and avatar_file.filename:
            cloud_url = current_app.config.get("CLOUDINARY_URL")
            if cloud_url:
                res = cloudinary.uploader.upload(avatar_file, resource_type="auto")
                current_user.avatar_url = res["secure_url"]
            else:
                filename = secure_filename(avatar_file.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                avatar_file.save(filepath)
                current_user.avatar_url = filepath
        elif avatar_url:
            current_user.avatar_url = avatar_url
        current_user.about = request.form.get("bio")
        current_user.career = request.form.get("career")
        current_user.interests = request.form.get("interests")
        db.session.commit()
        return redirect(url_for("feed.feed_home"))
    return render_template("onboarding/finish.html")


@bp.route("/pending")
@login_required
def pending():
    if current_user.activated:
        return redirect(url_for("feed.feed_home"))
    return render_template("onboarding/pending.html")


@bp.route("/resend", methods=["POST"])
@login_required
@limiter.limit(
    "3 per hour", key_func=_user_key, deduct_when=lambda r: request.method == "POST"
)
def resend():
    if current_user.activated:
        return redirect(url_for("feed.feed_home"))
    success, error = send_confirmation_email(current_user)
    if not success:
        flash(
            "No se pudo enviar el correo de confirmación. Inténtalo más tarde.",
            "danger",
        )
        if error:
            flash(error, "danger")
    record_auth_event(current_user, "resend_email")
    flash("Correo reenviado")
    return redirect(url_for("onboarding.pending"))


csrf.exempt(resend)


@bp.route("/change_email", methods=["GET", "POST"])
@login_required
def change_email():
    if request.method == "POST":
        new_email = request.form.get("email")
        if not new_email or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", new_email):
            flash("Ingresa un correo válido", "danger")
            return render_template("onboarding/change_email.html"), 400
        if User.query.filter_by(email=new_email).first():
            flash("Ese correo ya está registrado", "danger")
            return render_template("onboarding/change_email.html"), 400
        current_user.email = new_email
        current_user.activated = False
        db.session.commit()
        send_confirmation_email(current_user)
        flash(
            "Tu dirección de correo ha sido actualizada y se ha reenviado la verificación.",
            "success",
        )
        return redirect(url_for("onboarding.pending"))
    return render_template("onboarding/change_email.html")
