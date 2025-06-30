from alembic.command import upgrade
from alembic.config import Config
from sqlalchemy.exc import OperationalError
import pytest

from crunevo import create_app


def test_alembic_upgrade():
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        cfg = Config("alembic.ini")
        cfg.set_main_option("script_location", "migrations")
        try:
            upgrade(cfg, "head")
        except OperationalError as exc:
            if "IF NOT EXISTS" in str(exc):
                pytest.skip("SQLite without IF NOT EXISTS support")
            raise
