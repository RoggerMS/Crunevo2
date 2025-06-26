from datetime import date, timedelta
from crunevo.utils.login_history import record_login
from crunevo.constants import CreditReasons


def test_streak_awards_credits(db_session, test_user):
    day, credits = record_login(test_user, date.today())
    assert day == 1
    assert credits == 2
    assert test_user.credits == 2
    assert test_user.credit_history[-1].reason == CreditReasons.RACHA_LOGIN


def test_streak_resets_after_break(db_session, test_user):
    start = date.today() - timedelta(days=2)
    record_login(test_user, start)
    record_login(test_user, start + timedelta(days=1))
    record_login(test_user, start + timedelta(days=3))
    assert test_user.login_streak.current_day == 1
