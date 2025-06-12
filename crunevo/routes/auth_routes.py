from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from crunevo.utils.helpers import activated_required
from urllib.parse import urlparse  # ✅ Corrección aquí
from crunevo.extensions import db
from crunevo.models import User
from crunevo.utils import spend_credit, record_login
from crunevo.constants import CreditReasons

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registro exitoso. Inicia sesión")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            record_login(user)
            next_page = request.args.get("next")
            if not next_page or urlparse(next_page).netloc != "":
                next_page = url_for("feed.index")
            return redirect(next_page)
        flash("Credenciales inválidas")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@activated_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/perfil", methods=["GET", "POST"])
@activated_required
def perfil():
    if request.method == "POST":
        current_user.about = request.form.get("about")
        avatar_url = request.form.get("avatar_url")
        if avatar_url:
            current_user.avatar_url = avatar_url
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
