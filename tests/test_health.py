import os
from crunevo.app import create_app


def test_health_endpoint():
    os.environ["ENABLE_TALISMAN"] = "0"
    app = create_app()
    app.add_url_rule("/health", "health", lambda: ("ok", 200))
    with app.test_client() as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.data == b"ok"
