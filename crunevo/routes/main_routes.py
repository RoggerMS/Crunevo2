from flask import Blueprint, render_template, redirect, url_for, current_app
from flask_login import current_user
from crunevo.routes.feed_routes import feed_home

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_app.config.get("ADMIN_INSTANCE"):
            return redirect(url_for("admin.dashboard"))
        return feed_home()
    return redirect(url_for("auth.login"))


@main_bp.route("/terms")
def terms():
    return render_template("terms.html")


@main_bp.route("/terminos")
def terminos():
    return redirect(url_for("main.terms"))


@main_bp.route("/crolars")
def crolars():
    return render_template("crolars.html")


@main_bp.route("/tienda")
def tienda():
    return redirect("/store")


@main_bp.route("/privacidad")
def privacidad():
    return render_template("static/privacy.html")


@main_bp.route("/crunebot")
def redirect_crunebot():
    """Redirect legacy /crunebot to the unified IA chat."""
    return redirect(url_for("ia.ia_chat"))
