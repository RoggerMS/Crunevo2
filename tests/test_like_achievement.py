from crunevo.models import Note
from crunevo.constants import AchievementCodes


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_100_likes_unlocks_badge(client, db_session, test_user, another_user):
    note = Note(title="test", author=another_user, likes=99)
    db_session.add(note)
    db_session.commit()

    login(client, "tester", "secret")
    resp = client.post(f"/notes/{note.id}/like")
    assert resp.status_code == 200

    db_session.refresh(another_user)
    assert any(
        a.achievement.code == AchievementCodes.LIKE_100
        for a in another_user.achievements
    )
