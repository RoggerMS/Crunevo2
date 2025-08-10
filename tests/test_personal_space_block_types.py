def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_block_type_views(client, test_user):
    login(client, test_user.username)
    block_types = [
        "bitacora",
        "nota_enriquecida",
        "kanban",
        "objetivo",
        "tarea",
        "bloque_personalizado",
        "lista",
        "recordatorio",
        "frase",
        "enlace",
    ]
    for btype in block_types:
        resp = client.post(
            "/espacio-personal/api/blocks",
            json={"type": btype, "title": btype.capitalize()},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        block_id = data["block"]["id"]
        if btype == "kanban":
            view_path = f"/espacio-personal/kanban/{block_id}"
        else:
            view_path = f"/espacio-personal/bloque/{block_id}"
        view_resp = client.get(view_path, environ_overrides={"wsgi.url_scheme": "https"})
        
        assert view_resp.status_code == 200, f"{btype} returned {view_resp.status_code}"
