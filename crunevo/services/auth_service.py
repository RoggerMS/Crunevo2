from __future__ import annotations

import json
from urllib.parse import urlparse

from flask import url_for
from flask_login import login_user, current_user
from sqlalchemy import inspect

from crunevo.cache import login_attempts
from crunevo.extensions import db
from crunevo.models import User
from crunevo.utils import record_activity, record_login
from crunevo.utils.audit import record_auth_event


def authenticate_user(username: str, password: str, admin_mode: bool = False):
    """Return (user, error, wait) after verifying credentials."""
    if login_attempts.is_blocked(username):
        wait = login_attempts.get_remaining(username)
        return None, "blocked", wait

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_attempts.reset(username)
        if admin_mode and user.role not in ("admin", "moderator"):
            record_auth_event(
                user,
                "login_fail",
                extra=json.dumps({"username": username, "reason": "role"}),
            )
            return None, "role", 0
        record_auth_event(user, "login_success")
        return user, None, 0

    login_attempts.record_fail(username)
    if user:
        record_auth_event(user, "login_fail", extra=json.dumps({"username": username}))
    return None, "invalid", 0


def requires_two_factor(user: User) -> bool:
    """Return True if the user has a confirmed two factor record."""
    if not inspect(db.engine).has_table("two_factor_token"):
        return False
    try:
        record = user.two_factor
    except Exception:
        db.session.rollback()
        return False
    return bool(record and record.confirmed_at)


def finalize_login(user: User):
    """Log the user in and record login activity."""
    try:
        login_user(user)
        record_login(user)
        record_activity("login")
    except Exception as e:
        # Log the error but don't fail the login process
        import logging
        logging.error(f"Error in finalize_login: {e}")
        # Ensure user is still logged in even if activity recording fails
        if not current_user.is_authenticated:
            login_user(user)


def safe_next_page(next_page: str | None) -> str:
    if not next_page or urlparse(next_page).netloc != "":
        return url_for("feed.feed_home")
    return next_page
