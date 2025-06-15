"""Application package initializer."""

from .app import create_app as _create_app
from .routes import main_routes


def create_app():
    app = _create_app()
    app.register_blueprint(main_routes.main_bp)
    return app
