from crunevo.utils.achievements import unlock_achievement
from crunevo.constants import AchievementCodes


def test_unlock_achievement(db_session, test_user):
    unlock_achievement(test_user, AchievementCodes.PRIMER_APUNTE)
    assert any(
        a.achievement.code == AchievementCodes.PRIMER_APUNTE
        for a in test_user.achievements
    )


def test_share_unlocks_sharing_badge(db_session, test_user):
    unlock_achievement(test_user, AchievementCodes.COMPARTIDOR)
    assert any(
        a.achievement.code == AchievementCodes.COMPARTIDOR
        for a in test_user.achievements
    )


def test_downloads_unlocks_badge(db_session, test_user):
    from crunevo.models import Note

    note = Note(title="test", author=test_user)
    db_session.add(note)
    db_session.commit()

    for _ in range(100):
        note.downloads += 1
    db_session.commit()

    unlock_achievement(test_user, AchievementCodes.DESCARGA_100)

    assert any(
        a.achievement.code == AchievementCodes.DESCARGA_100
        for a in test_user.achievements
    )
