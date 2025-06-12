def test_alembic_upgrade(app):
    from alembic.config import Config
    from alembic.command import upgrade

    from crunevo.extensions import db

    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "migrations")

    with app.app_context():
        db.drop_all()
        upgrade(cfg, "head")
