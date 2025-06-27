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
)
from flask_login import login_user, current_user, login_required
import secrets

import cloudinary.uploader
from werkzeug.utils import secure_filename

from crunevo.extensions import db, limiter, csrf
from flask_limiter.util import get_remote_address
from zxcvbn import zxcvbn
from crunevo.models import User, EmailToken
from crunevo.utils.mailer import send_email
from crunevo.utils.audit import record_auth_event
from sqlalchemy.exc import IntegrityError

bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")


def generate_token():
    return secrets.token_urlsafe(32)


def send_confirmation_email(user):
    token = generate_token()
    db.session.add(EmailToken(token=token, email=user.email, user_id=user.id))
    db.session.commit()
    confirm_url = url_for("onboarding.confirm", token=token, _external=True)
    html = render_template("emails/confirm.html", confirm_url=confirm_url)
    return send_email(user.email, "¡Confirma tu cuenta en CRUNEVO!", html)


def _user_key():
    return current_user.get_id() or get_remote_address()


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("15 per hour", deduct_when=lambda r: request.method == "POST")
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if len(password) < 12 or zxcvbn(password)["score"] < 2:
            flash("Contraseña débil", "danger")
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

            referidor = User.query.filter_by(username=ref).first()
            if referidor:
                codigo = f"{referidor.username}-{user.username}"
                if not Referral.query.filter_by(code=codigo).first():
                    db.session.add(
                        Referral(
                            code=codigo,
                            invitador_id=referidor.id,
                            invitado_id=user.id,
                        )
                    )
                    db.session.commit()
        if not send_confirmation_email(user):
            flash(
                "No se pudo enviar el correo de confirmación. Inténtalo más tarde.",
                "danger",
            )
        return render_template("onboarding/confirm.html")
    return render_template("onboarding/register.html")


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
    db.session.commit()
    record_auth_event(record.user, "confirm_email")
    login_user(record.user)
    return redirect(url_for("onboarding.finish"))


@bp.route("/finish", methods=["GET", "POST"])
@login_required
def finish():
    if request.method == "POST":
        current_user.username = request.form.get("alias")
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
    if not send_confirmation_email(current_user):
        flash(
            "No se pudo enviar el correo de confirmación. Inténtalo más tarde.",
            "danger",
        )
    record_auth_event(current_user, "resend_email")
    flash("Correo reenviado")
    return redirect(url_for("onboarding.pending"))


csrf.exempt(resend)
