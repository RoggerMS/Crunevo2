from crunevo.models import User


def _get_csrf_token(page):
    import re
    import html

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
    db_session.add_all([admin, user])
    db_session.commit()

    client.post("/login", data={"username": "adm", "password": "pass"})
    client.application.config["WTF_CSRF_ENABLED"] = True

    page = client.get("/admin/verificaciones").data.decode()
    token = _get_csrf_token(page)

    assert client.post(f"/admin/verificaciones/{user.id}/approve").status_code == 400

    resp = client.post(
        f"/admin/verificaciones/{user.id}/approve",
        data={"csrf_token": token},
    )
    assert resp.status_code == 302
    db_session.refresh(user)
    assert user.verification_level == 2
