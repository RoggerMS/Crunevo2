from crunevo.models import User


def test_register_invalid_email(client):
    resp = client.post(
        "/onboarding/register",
        data={"email": "bademail", "password": "StrongPassw0rd!"},
    )
    assert resp.status_code == 400
    assert User.query.filter_by(email="bademail").first() is None
