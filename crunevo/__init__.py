"""Application package initializer."""

from .app import create_app as _create_app
from .routes import main_routes, static_routes
import os


def create_app():
    app = _create_app()

    if os.environ.get("ADMIN_INSTANCE") != "1":
        app.register_blueprint(main_routes.main_bp)
        app.register_blueprint(static_routes.static_bp)

    from crunevo.routes.saved_routes import saved_bp
    app.register_blueprint(saved_bp)

    from crunevo.routes.course_routes import course_bp
    app.register_blueprint(course_bp)

    return app