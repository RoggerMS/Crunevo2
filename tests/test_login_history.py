from datetime import date, timedelta
from crunevo.utils.login_history import record_login
from crunevo.constants import AchievementCodes


def test_login_streak_unlocks(db_session, test_user):
    start = date.today() - timedelta(days=6)
    for i in range(7):
        record_login(test_user, start + timedelta(days=i))

    assert any(
        a.achievement.code == AchievementCodes.CONECTADO_7D
        for a in test_user.achievements
    )


def test_login_streak_not_enough(db_session, test_user):
    start = date.today() - timedelta(days=5)
    for i in range(6):
        record_login(test_user, start + timedelta(days=i))

    assert not any(
        a.achievement.code == AchievementCodes.CONECTADO_7D
        for a in test_user.achievements
    )
