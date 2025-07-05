def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_activity_on_login(client, test_user):
    login(client, test_user.username)
    from crunevo.models import UserActivity

    act = UserActivity.query.filter_by(user_id=test_user.id, action="login").first()
    assert act is not None


def test_activity_on_post(client, test_user):
    login(client, test_user.username)
    client.post("/feed/post", data={"content": "hello"})
    from crunevo.models import UserActivity

    act = UserActivity.query.filter_by(
        action="post_created", user_id=test_user.id
    ).first()
    assert act is not None


def test_activity_page(client, test_user):
    login(client, test_user.username)
    client.post("/feed/post", data={"content": "hello"})
    resp = client.get("/dashboard/activity")
    assert resp.status_code == 200
    assert b"post_created" in resp.data
