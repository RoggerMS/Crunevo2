def test_healthz_endpoint(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
