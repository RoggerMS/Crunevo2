from crunevo.extensions import db


def test_healthz_returns_200_no_redirect(client, monkeypatch):
    called = []

    def fail_connect(*args, **kwargs):
        called.append(True)
        raise AssertionError("DB should not be accessed")

    monkeypatch.setattr(db.engine, "connect", fail_connect)
    resp = client.get("/healthz", follow_redirects=False)
    assert resp.status_code == 200
    assert b"Redirecting" not in resp.data
    assert not called


def test_live_and_ready(client):
    assert client.get("/live").status_code == 200
    assert client.get("/ready").status_code == 200
