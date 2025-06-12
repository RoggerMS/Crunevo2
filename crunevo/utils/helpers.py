from functools import wraps
from flask import redirect, url_for
from flask_login import current_user, login_required


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return redirect(url_for("feed.index"))
        return f(*args, **kwargs)

    return decorated_function


def activated_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.activated:
            return redirect(url_for("onboarding.register"))
        if current_user.username == current_user.email or not current_user.avatar_url:
            return redirect(url_for("onboarding.finish"))
        return f(*args, **kwargs)

    return decorated_function
