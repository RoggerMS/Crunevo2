def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_change_password_success(client, db_session, test_user):
    login(client, test_user.username)
    resp = client.post(
        "/configuracion/password",
        data={
            "current_password": "secret",
            "new_password": "newsecret",
            "confirm_new": "newsecret",
        },
    )
    assert resp.status_code == 200
    db_session.refresh(test_user)
    assert test_user.check_password("newsecret")


def test_change_password_wrong_current(client, db_session, test_user):
    login(client, test_user.username)
    resp = client.post(
        "/configuracion/password",
        data={
            "current_password": "wrong",
            "new_password": "newsecret",
            "confirm_new": "newsecret",
        },
    )
    assert resp.status_code == 400
    db_session.refresh(test_user)
    assert test_user.check_password("secret")


def test_change_password_mismatch(client, db_session, test_user):
    login(client, test_user.username)
    resp = client.post(
        "/configuracion/password",
        data={
            "current_password": "secret",
            "new_password": "newsecret",
            "confirm_new": "other",
        },
    )
    assert resp.status_code == 400
    db_session.refresh(test_user)
    assert test_user.check_password("secret")
