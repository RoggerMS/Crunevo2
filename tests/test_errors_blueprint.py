import os
from crunevo.app import create_app


def test_errors_blueprint_registered_once_public(monkeypatch):
    monkeypatch.delenv("ADMIN_INSTANCE", raising=False)
    os.environ["ENABLE_TALISMAN"] = "0"
    app = create_app()
    assert list(app.blueprints.keys()).count("errors") == 1


def test_errors_blueprint_registered_once_admin(monkeypatch):
    monkeypatch.setenv("ADMIN_INSTANCE", "1")
    os.environ["ENABLE_TALISMAN"] = "0"
    app = create_app()
    assert list(app.blueprints.keys()).count("errors") == 1
