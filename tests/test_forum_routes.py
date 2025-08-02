# -*- coding: utf-8 -*-


def test_foro_endpoint(client):
    response = client.get("/foro")
    assert response.status_code != 500, "La ruta /foro lanza error 500 inesperado"
