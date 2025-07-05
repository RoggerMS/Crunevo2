from crunevo.models import PageView, User, SiteConfig


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_pageview_recorded(client, db_session):
    resp = client.get("/terms")
    assert resp.status_code == 200
    view = PageView.query.one()
    assert view.path == "/terms"


def test_admin_pageviews_route(client, db_session, test_user):
    admin = User(
        username="admin",
        email="admin@example.com",
        role="admin",
        activated=True,
        avatar_url="a",
    )
    admin.set_password("pass")
    db_session.add(admin)
    db_session.commit()

    # generate some page views
    client.get("/terms")
    client.get("/terms")

    login(client, "admin", "pass")
    resp = client.get("/admin/pageviews")
    assert resp.status_code == 200
    assert b"/terms" in resp.data


def test_toggle_maintenance_persists(client, db_session):
    admin = User(
        username="ma",
        email="ma@example.com",
        role="admin",
        activated=True,
        avatar_url="a",
    )
    admin.set_password("pass")
    db_session.add(admin)
    db_session.commit()

    login(client, "ma", "pass")

    resp = client.post("/admin/toggle-maintenance")
    assert resp.status_code == 302
    cfg = SiteConfig.query.filter_by(key="maintenance_mode").first()
    assert cfg.value == "1"
    assert client.application.config["MAINTENANCE_MODE"] is True

    resp = client.post("/admin/toggle-maintenance")
    assert resp.status_code == 302
    cfg = SiteConfig.query.filter_by(key="maintenance_mode").first()
    assert cfg.value == "0"
    assert client.application.config["MAINTENANCE_MODE"] is False
