def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_ia_requires_login(client):
    resp = client.get("/ia")
    assert resp.status_code in (302, 308)


def test_ia_access(client, test_user):
    login(client, test_user.username)
    resp = client.get("/ia/")
    assert resp.status_code == 200
    assert b"ChatCrunevo" in resp.data


def test_notes_populares_redirect(client, test_user):
    login(client, test_user.username)
    resp = client.get("/notes/populares")
    assert resp.status_code == 302


def test_ia_ask_disabled(client, test_user):
    login(client, test_user.username)
    resp = client.post("/ia/ask", json={"message": "¿Cómo ganar Crolars?"})
    data = resp.get_json()
    assert "Crolars" in data["answer"]
