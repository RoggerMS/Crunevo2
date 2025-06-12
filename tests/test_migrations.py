from alembic.command import upgrade
from alembic.config import Config
from crunevo.app import create_app


def test_alembic_upgrade():
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        cfg = Config("alembic.ini")
        upgrade(cfg, "head")
