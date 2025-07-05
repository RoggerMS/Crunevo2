from crunevo.models import Notification, User
from crunevo.utils import send_notification


def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_api_notifications(client, db_session, test_user):
    n = Notification(user_id=test_user.id, message="Hola")
    db_session.add(n)
    db_session.commit()
    login(client, test_user.username)
    resp = client.get("/api/notifications")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data[0]["message"] == "Hola"


def test_mark_all_read(client, db_session, test_user):
    db_session.add(Notification(user_id=test_user.id, message="A"))
    db_session.add(Notification(user_id=test_user.id, message="B"))
    db_session.commit()
    login(client, test_user.username)
    resp = client.post("/notifications/read_all")
    assert resp.status_code == 200
    assert (
        Notification.query.filter_by(user_id=test_user.id, is_read=False).count() == 0
    )


def test_send_notification_filter(db_session):
    u1 = User(
        username="law",
        email="law@example.com",
        activated=True,
        avatar_url="a",
        career="law",
    )
    u1.set_password("secret")
    u2 = User(
        username="eng",
        email="eng@example.com",
        activated=True,
        avatar_url="a",
        career="engineering",
    )
    u2.set_password("secret")
    db_session.add_all([u1, u2])
    db_session.commit()

    send_notification(message="Hola", career="law")

    assert Notification.query.filter_by(user_id=u1.id).count() == 1
    assert Notification.query.filter_by(user_id=u2.id).count() == 0
