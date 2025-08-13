def login(client, username, password="secret"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_block_type_views(client, test_user):
    login(client, test_user.username)
    block_types = [
        "nota",
        "tarea",
        "objetivo",
        "lista",
    ]
    for btype in block_types:
        resp = client.post(
            "/api/personal-space/blocks",
            json={"type": btype, "title": btype.capitalize()},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        block_id = data["block"]["id"]
        view_path = f"/personal-space/block/{block_id}"
        view_resp = client.get(view_path, environ_overrides={"wsgi.url_scheme": "https"})
        
        assert view_resp.status_code == 200, f"{btype} returned {view_resp.status_code}"
