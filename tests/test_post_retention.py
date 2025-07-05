from crunevo.models import User, SiteConfig


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_set_post_retention(client, db_session, test_user):
    admin = User(
        username="admret",
        email="admret@example.com",
        role="admin",
        activated=True,
        avatar_url="a",
    )
    admin.set_password("pass")
    db_session.add(admin)
    db_session.commit()

    login(client, "admret", "pass")
    resp = client.post("/admin/set-post-retention", data={"days": "45"})
    assert resp.status_code == 302
    cfg = SiteConfig.query.filter_by(key="post_retention_days").first()
    assert cfg.value == "45"
    assert client.application.config["POST_RETENTION_DAYS"] == 45
