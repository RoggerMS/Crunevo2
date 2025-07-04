def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_api_user_returns_status(client, test_user):
    login(client, test_user.username)
    resp = client.get("/api/user")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["activated"] is True
    assert data["username"] == test_user.username
