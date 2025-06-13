from crunevo.models import User


def test_onboarding_register_duplicate_email(client, db_session):
    user = User(username="dup", email="dup@example.com")
    user.set_password("StrongPassw0rd!")
    db_session.add(user)
    db_session.commit()

    resp = client.post(
        "/onboarding/register",
        data={"email": "dup@example.com", "password": "StrongPassw0rd!"},
    )
    assert resp.status_code == 400
    assert User.query.filter_by(email="dup@example.com").count() == 1


def test_auth_register_duplicate_username(client, db_session):
    user = User(username="dupuser", email="dupuser@example.com", activated=True)
    user.set_password("StrongPassw0rd!")
    db_session.add(user)
    db_session.commit()

    resp = client.post(
        "/register",
        data={
            "username": "dupuser",
            "email": "other@example.com",
            "password": "StrongPassw0rd!",
        },
    )
    assert resp.status_code == 400
    assert User.query.filter_by(username="dupuser").count() == 1
