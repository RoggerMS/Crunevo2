from crunevo.models import User, Note, VerificationRequest
import html
import re


def test_badge_visible(client, db_session):
    user = User(
        username="v",
        email="v@example.com",
        activated=True,
        avatar_url="a",
        verification_level=2,
    )
    user.set_password("StrongPassw0rd!")
    db_session.add(user)
    db_session.commit()
    client.post("/login", data={"username": "v", "password": "StrongPassw0rd!"})
    resp = client.get("/perfil")
    assert b"bi-check-circle-fill" in resp.data


def test_badge_hidden(client, db_session):
    user = User(username="n", email="n@example.com", activated=True, avatar_url="a")
    user.set_password("StrongPassw0rd!")
    db_session.add(user)
    db_session.commit()
    client.post("/login", data={"username": "n", "password": "StrongPassw0rd!"})
    resp = client.get("/perfil")
    assert b"bi-check-circle-fill" not in resp.data


def test_admin_can_approve(client, db_session):
    admin = User(
        username="adm",
        email="adm@example.com",
        role="admin",
        activated=True,
        avatar_url="a",
    )
    admin.set_password("pass")
    user = User(
        username="stud", email="stud@example.com", activated=True, avatar_url="a"
    )
    user.set_password("pass")
    req = VerificationRequest(user=user, info="docs")
    db_session.add_all([admin, user, req])
    db_session.commit()
    client.post("/login", data={"username": "adm", "password": "pass"})
    client.post(f"/admin/verificaciones/{req.id}/approve")
    db_session.refresh(user)
    assert user.verification_level == 2
    client.post("/login", data={"username": "stud", "password": "pass"})
    resp = client.get("/perfil")
    assert b"bi-check-circle-fill" in resp.data


def test_download_requires_verification(client, db_session):
    user = User(username="d", email="d@example.com", activated=True, avatar_url="a")
    user.set_password("pass")
    db_session.add(user)
    db_session.commit()
    note = Note(title="t", filename="static/uploads/demo.pdf", author=user)
    db_session.add(note)
    db_session.commit()
    client.post("/login", data={"username": "d", "password": "pass"})
    resp = client.get(f"/notes/{note.id}/download")
    assert resp.status_code == 302
    assert note.filename not in resp.headers.get("Location", "")
    user.verification_level = 2
    db_session.commit()
    client.post("/login", data={"username": "d", "password": "pass"})
    resp = client.get(f"/notes/{note.id}/download")
    assert resp.headers["Location"].endswith(note.filename)


def _get_csrf_token(page):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html.unescape(page))
    return m.group(1) if m else None


def test_admin_verification_csrf(client, db_session):
    admin = User(
        username="adm",
        email="adm@example.com",
        role="admin",
        activated=True,
        avatar_url="a",
    )
    admin.set_password("pass")
    user = User(
        username="stud",
        email="stud@example.com",
        activated=True,
        avatar_url="b",
    )
    user.set_password("pass")
    req = VerificationRequest(user=user, info="docs")
    db_session.add_all([admin, user, req])
    db_session.commit()

    client.post("/login", data={"username": "adm", "password": "pass"})
    with client.application.app_context():
        client.application.config.update(WTF_CSRF_ENABLED=True)

        page = client.get("/admin/verificaciones").data.decode()
        token = _get_csrf_token(page)

        assert client.post(f"/admin/verificaciones/{req.id}/approve").status_code == 302

        resp = client.post(
            f"/admin/verificaciones/{req.id}/approve",
            data={"csrf_token": token},
        )
        assert resp.status_code == 302
        user = db_session.get(User, user.id)
        assert user.verification_level == 2


def test_submit_and_approve_request(client, db_session):
    admin = User(
        username="adm",
        email="adm@example.com",
        role="admin",
        activated=True,
        avatar_url="a",
    )
    admin.set_password("pass")
    user = User(username="req", email="req@example.com", activated=True, avatar_url="b")
    user.set_password("pass")
    db_session.add_all([admin, user])
    db_session.commit()

    client.post("/login", data={"username": "req", "password": "pass"})
    resp = client.post(
        "/configuracion/verificacion",
        data={"info": "docs"},
    )
    assert resp.json.get("success")
    db_session.refresh(user)
    assert user.verification_level == 1
    req = VerificationRequest.query.filter_by(user_id=user.id).first()
    assert req is not None

    client.post("/login", data={"username": "adm", "password": "pass"})
    client.post(f"/admin/verificaciones/{req.id}/approve")
    db_session.refresh(user)
    db_session.refresh(req)
    assert user.verification_level == 2
    assert req.status == "approved"
