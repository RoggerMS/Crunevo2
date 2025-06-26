from datetime import date, timedelta
from crunevo.models import LoginHistory
from crunevo.extensions import db
from crunevo.utils.achievements import unlock_achievement
from crunevo.constants import AchievementCodes
from .login_streak import handle_login_streak


def record_login(user, login_date=None):
    """Store a login date, update streak and unlock achievement.

    Returns the current streak day.
    """
    if login_date is None:
        login_date = date.today()

    exists = LoginHistory.query.filter_by(
        user_id=user.id, login_date=login_date
    ).first()
    if not exists:
        entry = LoginHistory(user_id=user.id, login_date=login_date)
        db.session.add(entry)
        db.session.commit()
    day = handle_login_streak(user, login_date)

    last_entries = (
        LoginHistory.query.filter_by(user_id=user.id)
        .order_by(LoginHistory.login_date.desc())
        .limit(7)
        .all()
    )

    if len(last_entries) >= 7:
        expected = login_date
        for item in last_entries:
            if item.login_date != expected:
                break
            expected -= timedelta(days=1)
        else:
            unlock_achievement(user, AchievementCodes.CONECTADO_7D)

    return day
