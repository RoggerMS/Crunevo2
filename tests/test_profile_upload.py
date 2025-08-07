import io


def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_upload_profile_picture(client, app, test_user, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    login(client, test_user.username)

    data = {"avatar": (io.BytesIO(b"avatar"), "avatar.png")}
    resp = client.post("/auth/upload-profile-picture", data=data)

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["success"] is True
    assert payload["avatarUrl"]


def test_upload_banner(client, app, test_user, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    login(client, test_user.username)

    data = {"banner": (io.BytesIO(b"banner"), "banner.png")}
    resp = client.post("/auth/upload-banner", data=data)

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["success"] is True
    assert payload["bannerUrl"]
