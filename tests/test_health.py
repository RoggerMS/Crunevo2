import os
from crunevo.app import create_app


def test_health_endpoint():
    os.environ["ENABLE_TALISMAN"] = "1"
    app = create_app()
    with app.test_client() as client:
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.data == b"ok"
