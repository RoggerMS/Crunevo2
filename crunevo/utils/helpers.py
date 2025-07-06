from functools import wraps
from datetime import datetime
from flask import redirect, url_for, flash
from flask_login import current_user, login_required
from crunevo.models import User
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect

from crunevo.extensions import db


def table_exists(table_name: str) -> bool:
    """Return True if the given table exists in the database."""
    try:
        return inspect(db.engine).has_table(table_name)
    except SQLAlchemyError:
        return False


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role not in ("admin", "moderator"):
            return redirect(url_for("feed.feed_home"))
        return f(*args, **kwargs)

    return decorated_function


def full_admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != "admin":
            return redirect(url_for("feed.feed_home"))
        return f(*args, **kwargs)

    return decorated_function


def activated_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if table_exists("user"):
            user = User.query.get(current_user.id)
            if not user or not user.activated:
                flash("Debes activar tu cuenta para acceder a esta función.", "warning")
                return redirect(url_for("onboarding.pending"))
        return f(*args, **kwargs)

    return decorated_function


def career_required(f):
    """Decorator to ensure user has a career assigned"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.career:
            flash("Debes asignar una carrera para acceder a esta función.", "warning")
            return redirect(url_for("auth.perfil") + "?tab=personal")
        return f(*args, **kwargs)

    return decorated_function


def get_available_careers():
    """Get list of available careers"""
    return [
        "Ingeniería de Sistemas",
        "Ingeniería Industrial",
        "Ingeniería Civil",
        "Administración de Empresas",
        "Contabilidad",
        "Marketing",
        "Psicología",
        "Derecho",
        "Medicina",
        "Enfermería",
        "Arquitectura",
        "Diseño Gráfico",
        "Comunicaciones",
        "Educación",
        "Economía",
    ]


def verified_required(f):
    @wraps(f)
    @activated_required
    def decorated(*args, **kwargs):
        if current_user.verification_level < 2:
            from flask import flash

            flash(
                "Necesitas verificación de estudiante para descargar apuntes",
                "warning",
            )
            return redirect(url_for("feed.feed_home"))
        return f(*args, **kwargs)

    return decorated


def get_hall_membership(user):
    """Return hall membership or None if table is missing."""
    try:
        from crunevo.models.hall_1000 import CrolarsHallMember

        return CrolarsHallMember.query.filter_by(user_id=user.id).first()
    except SQLAlchemyError:
        db.session.rollback()
        return None


def timesince(dt):
    """Return human readable delta from now in Spanish."""
    if not dt:
        return ""
    now = datetime.utcnow()
    if dt.tzinfo is not None:
        now = now.replace(tzinfo=dt.tzinfo)
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "hace unos segundos"
    minutes = seconds // 60
    if minutes < 60:
        return f"hace {minutes} minuto{'s' if minutes != 1 else ''}"
    hours = minutes // 60
    if hours < 24:
        return f"hace {hours} hora{'s' if hours != 1 else ''}"
    days = hours // 24
    return f"hace {days} d\u00eda{'s' if days != 1 else ''}"
