def test_terms_page(client):
    resp = client.get("/terms")
    assert resp.status_code == 200
    assert b"T\xc3\x89RMINOS Y CONDICIONES DE USO DE CRUNEVO" in resp.data
