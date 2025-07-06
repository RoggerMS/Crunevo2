from crunevo.models import User
from crunevo.extensions import mail


def test_register_short_password(client):
    resp = client.post(
        "/onboarding/register",
        data={"email": "weak@example.com", "password": "short"},
    )
    assert resp.status_code == 400
    assert User.query.filter_by(email="weak@example.com").first() is None


def test_register_strong_password(client):
    with mail.record_messages() as outbox:
        resp = client.post(
            "/onboarding/register",
            data={"email": "ok@example.com", "password": "StrongPassw0rd!"},
        )
        assert resp.status_code == 302
        assert len(outbox) == 1
    assert User.query.filter_by(email="ok@example.com").first() is not None
