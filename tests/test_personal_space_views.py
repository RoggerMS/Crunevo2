from crunevo.models import User


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
