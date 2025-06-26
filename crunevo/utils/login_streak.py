from datetime import date, timedelta
from crunevo.extensions import db
from crunevo.models import LoginStreak
from crunevo.constants import CreditReasons
from .credits import add_credit

STREAK_REWARDS = {
    1: 2,
    2: 3,
    3: 4,
    4: 5,
    5: 6,
    6: 7,
    7: 10,
}


def handle_login_streak(user, login_date=None):
    """Update or create streak, award credits and return (day, credits)."""
    if login_date is None:
        login_date = date.today()

    streak = LoginStreak.query.filter_by(user_id=user.id).first()
    if not streak:
        streak = LoginStreak(
            user_id=user.id,
            current_day=1,
            last_login=login_date,
            streak_start=login_date,
        )
        db.session.add(streak)
        db.session.commit()
        credits = STREAK_REWARDS[1]
        add_credit(user, credits, CreditReasons.RACHA_LOGIN)
        return 1, credits

    if streak.last_login == login_date:
        return streak.current_day, 0

    yesterday = login_date - timedelta(days=1)
    if streak.last_login == yesterday:
        streak.current_day += 1
    else:
        streak.current_day = 1
        streak.streak_start = login_date

    if streak.current_day > 7:
        streak.current_day = 1
        streak.streak_start = login_date

    streak.last_login = login_date
    db.session.commit()
    credits = STREAK_REWARDS[streak.current_day]
    add_credit(user, credits, CreditReasons.RACHA_LOGIN)
    return streak.current_day, credits
