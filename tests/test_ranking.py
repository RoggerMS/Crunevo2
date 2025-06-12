from crunevo.utils.ranking import calculate_weekly_ranking
from crunevo.models import RankingCache, Note, Credit
from crunevo.constants import AchievementCodes


def test_calculate_weekly_ranking(client, test_user):
    # crea una nota y un crédito para que el usuario obtenga puntaje
    note = Note(title="test", author=test_user)
    credit = Credit(user_id=test_user.id, amount=1, reason="test")
    from crunevo.extensions import db
    db.session.add_all([note, credit])
    db.session.commit()
    calculate_weekly_ranking()
    ranking = RankingCache.query.filter_by(user_id=test_user.id).first()
    assert ranking is not None
    assert ranking.score >= 0
    assert any(a.badge_code == AchievementCodes.TOP_3 for a in test_user.achievements)
