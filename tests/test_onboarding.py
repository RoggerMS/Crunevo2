from crunevo.models import User, EmailToken
from crunevo.extensions import mail


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_register_creates_inactive(client):
    with mail.record_messages() as outbox:
        client.post(
            "/onboarding/register",
            data={"email": "new@example.com", "password": "StrongPassw0rd!"},
        )
        user = User.query.filter_by(email="new@example.com").first()
        assert user is not None
        assert not user.activated
        assert len(outbox) == 1


def test_confirm_activates(client, db_session):
    user = User(username="temp", email="temp@example.com")
    user.set_password("StrongPassw0rd!")
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
    user.set_password("StrongPassw0rd!")
    db_session.add(user)
    db_session.commit()
    login(client, user.username, "StrongPassw0rd!")
    client.post(
        "/onboarding/finish",
        data={"alias": "alias", "avatar_url": "url", "bio": "bio"},
    )
    db_session.refresh(user)
    assert user.username == "alias"
    assert user.avatar_url == "url"
    assert user.about == "bio"


def test_resend_adds_email(client, db_session):
    user = User(username="res", email="res@example.com")
    user.set_password("StrongPassw0rd!")
    db_session.add(user)
    db_session.commit()
    login(client, user.username, "StrongPassw0rd!")
    with mail.record_messages() as outbox:
        client.post("/onboarding/resend")
        assert len(outbox) == 1


def test_token_expires(client, db_session):
    from freezegun import freeze_time
    from datetime import timedelta

    user = User(username="exp", email="exp@example.com")
    user.set_password("StrongPassw0rd!")
    db_session.add(user)
    db_session.commit()
    token = EmailToken(user_id=user.id, email=user.email)
    db_session.add(token)
    db_session.commit()
    with freeze_time(token.created_at + timedelta(seconds=3601)):
        resp = client.get(f"/onboarding/confirm/{token.token}")
    assert resp.status_code == 302
    assert not user.activated


def test_generated_token_length_and_confirm(client):
    with mail.record_messages():
        client.post(
            "/onboarding/register",
            data={"email": "tok@test.com", "password": "StrongPassw0rd!"},
        )
    user = User.query.filter_by(email="tok@test.com").first()
    token = EmailToken.query.filter_by(user_id=user.id).first()
    assert len(token.token) < 64
    client.get(f"/onboarding/confirm/{token.token}")
    assert user.activated
