from crunevo.utils.achievements import unlock_achievement
from crunevo.constants import AchievementCodes
from crunevo.models import UserAchievement


def test_unlock_achievement(db_session, test_user):
    unlock_achievement(test_user, AchievementCodes.PRIMER_APUNTE)
    assert any(a.badge_code == AchievementCodes.PRIMER_APUNTE for a in test_user.achievements)

