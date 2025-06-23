from functools import wraps
from datetime import datetime
from flask import redirect, url_for
from flask_login import current_user, login_required


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
        if not current_user.activated:
            return redirect(url_for("onboarding.pending"))
        if current_user.username == current_user.email or not current_user.avatar_url:
            return redirect(url_for("onboarding.finish"))
        return f(*args, **kwargs)

    return decorated_function


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
