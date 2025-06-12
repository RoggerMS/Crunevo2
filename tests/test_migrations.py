from alembic.config import Config
from alembic.command import upgrade
import os
from crunevo.app import create_app


def test_alembic_upgrade():
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    app = create_app()
    with app.app_context():
        cfg = Config("alembic.ini")
        upgrade(cfg, "head")
