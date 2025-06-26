from datetime import date, timedelta
from crunevo.extensions import db
from crunevo.models import LoginStreak

STREAK_REWARDS = {
    1: 2,
    2: 3,
    3: 4,
    4: 5,
    5: 6,
    6: 7,
    7: 10,
}


def streak_reward(day):
    """Return credits for a given streak day."""
    return STREAK_REWARDS.get(day, 2)


def handle_login_streak(user, login_date=None):
    """Update or create streak and return the current day."""
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
        return 1

    if streak.last_login == login_date:
        return streak.current_day

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
    return streak.current_day
