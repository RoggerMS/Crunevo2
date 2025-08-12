from crunevo.models.block import Block


def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_personal_space_views(client, test_user):
    login(client, test_user.username)
    paths = [
        "/espacio-personal/",
        "/espacio-personal/calendario",
        "/espacio-personal/estadisticas",
        "/espacio-personal/plantillas",
        "/espacio-personal/configuracion",
        "/espacio-personal/buscar",
        "/espacio-personal/papelera",
    ]
    for path in paths:
        resp = client.get(path, environ_overrides={"wsgi.url_scheme": "https"})
        assert resp.status_code == 200


def test_apply_template_by_slug(client, test_user):
    login(client, test_user.username)
    resp = client.post(
        "/espacio-personal/plantillas/aplicar/university-student",
        environ_overrides={"wsgi.url_scheme": "https"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"]


def test_view_objective_detail(client, db_session, test_user):
    block = Block(user_id=test_user.id, type="objetivo", title="Goal")
    block.set_metadata({"objective": {"title": "Goal", "milestones": [], "resources": []}})
    db_session.add(block)
    db_session.commit()

    login(client, test_user.username)
    resp = client.get(f"/espacio-personal/bloque/{block.id}")
    assert resp.status_code == 200
    assert b"objective-page" in resp.data
