def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_personal_space_views(client, test_user):
    login(client, test_user.username)
    paths = [
        "/personal-space/",
        "/personal-space/calendario",
        "/personal-space/estadisticas",
        "/personal-space/templates",
        "/personal-space/configuracion",
        "/personal-space/buscar",
        "/personal-space/papelera",
    ]
    for path in paths:
        resp = client.get(path, environ_overrides={"wsgi.url_scheme": "https"})
        assert resp.status_code == 200


def test_apply_template_by_slug(client, test_user):
    login(client, test_user.username)
    resp = client.post(
        "/personal-space/templates/aplicar/university-student",
        environ_overrides={"wsgi.url_scheme": "https"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"]
