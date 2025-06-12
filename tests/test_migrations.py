def test_alembic_upgrade(app):
    from alembic.config import Config
    from alembic.command import upgrade
    from crunevo.app import create_app

    migr_app = create_app()
    migr_app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")

    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "migrations")

    with migr_app.app_context():
        upgrade(cfg, "head")
