from crunevo.models import AuthEvent


def test_logout_event(client, db_session, test_user):
    # Login first
    client.post("/login", data={"username": test_user.username, "password": "secret"})
    client.get("/logout")
    event = AuthEvent.query.filter_by(user_id=test_user.id, event_type="logout").first()
    assert event is not None
