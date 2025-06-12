from crunevo.models import User, EmailToken
from crunevo.extensions import mail


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_register_creates_inactive(client):
    with mail.record_messages() as outbox:
        client.post(
            "/onboarding/register", data={"email": "new@example.com", "password": "pw"}
        )
        user = User.query.filter_by(email="new@example.com").first()
        assert user is not None
        assert not user.activated
        assert len(outbox) == 1


def test_confirm_activates(client, db_session):
    user = User(username="temp", email="temp@example.com")
    user.set_password("pw")
    db_session.add(user)
    db_session.commit()
    token = EmailToken(user_id=user.id, email=user.email)
    db_session.add(token)
    db_session.commit()
    client.get(f"/onboarding/confirm/{token.token}")
    assert user.activated
    assert token.consumed_at is not None


def test_finish_profile_persists(client, db_session):
    user = User(username="tmp", email="tmp@example.com", activated=True)
    user.set_password("pw")
    db_session.add(user)
    db_session.commit()
    login(client, user.username, "pw")
    client.post(
        "/onboarding/finish", data={"alias": "alias", "avatar": "url", "bio": "bio"}
    )
    db_session.refresh(user)
    assert user.username == "alias"
    assert user.avatar_url == "url"
    assert user.about == "bio"
