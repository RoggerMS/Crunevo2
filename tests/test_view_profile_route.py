from crunevo.models import Note, User
from flask import template_rendered
import contextlib


@contextlib.contextmanager
def captured_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


def create_user(username, email):
    user = User(username=username, email=email, activated=True, avatar_url="a")
    user.set_password("pass")
    return user


def test_view_profile_existing_user(client, db_session):
    user = create_user("alice", "alice@example.com")
    db_session.add(user)
    db_session.commit()
    client.post("/login", data={"username": "alice", "password": "pass"})
    resp = client.get("/perfil/alice")
    assert resp.status_code == 200


def test_view_profile_not_found(client, db_session, caplog):
    viewer = create_user("bob", "bob@example.com")
    db_session.add(viewer)
    db_session.commit()
    client.post("/login", data={"username": "bob", "password": "pass"})
    with caplog.at_level("WARNING"):
        resp = client.get("/perfil/missing")
    assert resp.status_code == 404
    assert "User missing not found" in caplog.text


def test_view_profile_null_verification_level(client, db_session):
    user = create_user("charlie", "charlie@example.com")
    user.verification_level = None
    db_session.add(user)
    db_session.commit()
    client.post("/login", data={"username": "charlie", "password": "pass"})
    resp = client.get("/perfil/charlie")
    assert resp.status_code == 200


def test_view_profile_with_note_ratings(client, db_session, app):
    user = create_user("dave", "dave@example.com")
    db_session.add(user)
    db_session.commit()

    note = Note(title="n1", user_id=user.id)
    note.rating = [4, 5]
    db_session.add(note)
    db_session.commit()

    client.post("/login", data={"username": "dave", "password": "pass"})
    with captured_templates(app) as templates:
        resp = client.get("/perfil/dave")
        assert resp.status_code == 200
        template, context = templates[0]
        assert context["average_rating"] == 4.5


def test_view_profile_achievements_progress(client, db_session, app):
    user = create_user("eve", "eve@example.com")
    db_session.add(user)
    db_session.commit()

    client.post("/login", data={"username": "eve", "password": "pass"})
    with captured_templates(app) as templates:
        resp = client.get("/perfil/eve?tab=logros")
        assert resp.status_code == 200
        template, context = templates[0]
        assert context["unlocked_count"] == 0
