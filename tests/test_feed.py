from crunevo.models import Note, FeedItem
from crunevo.utils.feed import create_feed_item_for_all
from crunevo.utils.achievements import unlock_achievement
from crunevo.utils.credits import add_credit, spend_credit
from flask_login import login_user
from flask_migrate import upgrade, downgrade
from crunevo.app import create_app


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_feed_shows_note_for_other_user(client, db_session, test_user, another_user):
    note = Note(title="Feed note", author=test_user)
    db_session.add(note)
    db_session.commit()
    create_feed_item_for_all("apunte", note.id)

    login(client, another_user.username, "secret")
    resp = client.get("/api/feed")
    assert resp.status_code == 200
    data = resp.get_json()[0]
    assert data["item_type"] == "apunte"
    assert data["title"] == "Feed note"


def test_feed_includes_achievement_event(client, db_session, test_user, another_user):
    unlock_achievement(test_user, "badge_test")
    login(client, another_user.username, "secret")
    resp = client.get("/api/feed")
    assert resp.status_code == 200
    types = [d["item_type"] for d in resp.get_json()]
    assert "logro" in types


def test_self_spend_no_movement_feed(app, db_session, test_user):
    with app.test_request_context("/"):
        login_user(test_user)
        add_credit(test_user, 5, "test")
        spend_credit(test_user, 2, "test")
    assert FeedItem.query.count() == 0


def test_migrations_upgrade_downgrade():
    migr_app = create_app()
    migr_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    migr_app.config["TESTING"] = True

    with migr_app.app_context():
        upgrade()
        downgrade(revision="base")
