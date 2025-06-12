from datetime import datetime, timedelta
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
from itsdangerous import URLSafeTimedSerializer

from crunevo.extensions import db, limiter, csrf
from flask_limiter.util import get_remote_address
from zxcvbn import zxcvbn
from crunevo.models import User, EmailToken
from crunevo.utils.mailer import send_email
from crunevo.utils.audit import record_auth_event

bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")


def generate_token(email):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email)


def send_confirmation_email(user):
    token = generate_token(user.email)
    db.session.add(EmailToken(token=token, email=user.email, user_id=user.id))
    db.session.commit()
    html = render_template("emails/confirm.html", token=token)
    send_email(user.email, "Confirma tu cuenta", html)


def _user_key():
    return current_user.get_id() or get_remote_address()


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per hour")
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
        db.session.commit()
        send_confirmation_email(user)
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
        current_user.avatar_url = request.form.get("avatar")
        current_user.about = request.form.get("bio")
        db.session.commit()
        return redirect(url_for("feed.index"))
    return render_template("onboarding/finish.html")


@bp.route("/pending")
@login_required
def pending():
    if current_user.activated:
        return redirect(url_for("feed.index"))
    return render_template("onboarding/pending.html")


@bp.route("/resend", methods=["POST"])
@login_required
@limiter.limit("3 per hour", key_func=_user_key)
def resend():
    if current_user.activated:
        return redirect(url_for("feed.index"))
    send_confirmation_email(current_user)
    record_auth_event(current_user, "resend_email")
    flash("Correo reenviado")
    return redirect(url_for("onboarding.pending"))


csrf.exempt(resend)
