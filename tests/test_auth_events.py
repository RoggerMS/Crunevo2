from crunevo.models import User, AuthEvent


def test_login_success_event(client, db_session):
    user = User(
        username="audit", email="audit@example.com", activated=True, avatar_url="a"
    )
    user.set_password("StrongPassw0rd!")
    db_session.add(user)
    db_session.commit()
    client.post(
        "/login", data={"username": user.username, "password": "StrongPassw0rd!"}
    )
    event = AuthEvent.query.filter_by(
        user_id=user.id, event_type="login_success"
    ).first()
    assert event is not None


def test_login_fail_event(client):
    client.post("/login", data={"username": "nosuch", "password": "bad"})
    event = AuthEvent.query.filter_by(event_type="login_fail").first()
    assert event is not None
