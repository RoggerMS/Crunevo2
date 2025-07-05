def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_recent_posts_requires_api_key(client):
    resp = client.get("/api/recent-posts")
    assert resp.status_code == 401


def test_generate_key_and_access(client, test_user, db_session):
    login(client, test_user.username)
    resp = client.post("/api/generate-key")
    assert resp.status_code == 200
    key = resp.get_json()["api_key"]
    resp2 = client.get("/api/recent-posts", headers={"X-API-Key": key})
    assert resp2.status_code == 200
