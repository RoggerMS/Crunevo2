from flask import Flask, request, redirect, url_for, flash
import logging
from logging.handlers import RotatingFileHandler
import os

from .extensions import db, login_manager, migrate, mail, csrf, limiter
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFError

DEFAULT_CSP = {
    "default-src": "'self'",
    "img-src": ["'self'", "data:", "https://res.cloudinary.com"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "script-src": ["'self'", "'unsafe-inline'"],
    "connect-src": "'self'",
}


def create_app():
    app = Flask(__name__)
    from .config import Config

    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter._storage_uri = app.config.get("RATELIMIT_STORAGE_URI")
    limiter.init_app(app)
    if app.config.get("ENABLE_TALISMAN", True):
        csp = app.config.get("TALISMAN_CSP", DEFAULT_CSP)
        if app.config.get("ENABLE_CSP_OVERRIDE"):
            csp = None
        Talisman(
            app,
            content_security_policy=csp,
            force_https=True,
            strict_transport_security=True,
        )
    login_manager.login_view = "onboarding.register"

    migrate.init_app(app, db)

    from .routes.onboarding_routes import bp as onboarding_bp
    from .routes.auth_routes import auth_bp
    from .routes.notes_routes import notes_bp
    from .routes.feed_routes import feed_bp
    from .routes.store_routes import store_bp
    from .routes.chat_routes import chat_bp
    from .routes.admin_routes import admin_bp
    from .routes.admin_blocker import admin_blocker_bp
    from .routes.ranking_routes import ranking_bp
    from .routes.errors import errors_bp
    from .routes.health_routes import health_bp

    is_admin = os.environ.get("ADMIN_INSTANCE") == "1"
    testing_env = os.environ.get("PYTEST_CURRENT_TEST") is not None
    app.config["ADMIN_INSTANCE"] = is_admin

    app.register_blueprint(health_bp)
    app.logger.info("Running in ADMIN mode" if is_admin else "Running in PUBLIC mode")

    if is_admin:
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp)
        app.register_blueprint(errors_bp)
    else:
        app.register_blueprint(onboarding_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(notes_bp)
        app.register_blueprint(feed_bp)
        app.register_blueprint(store_bp)
        app.register_blueprint(chat_bp)
        app.register_blueprint(ranking_bp)
        app.register_blueprint(errors_bp)
        app.register_blueprint(admin_blocker_bp)
        if testing_env:
            app.register_blueprint(admin_bp)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash("La sesión expiró, vuelve a intentarlo.", "danger")
        return redirect(request.referrer or url_for("feed.index")), 302

    if os.getenv("SCHEDULER") == "1":
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from .jobs.decay import decay_scores
        from .jobs.cleanup_auth_events import cleanup_auth_events

        scheduler = BackgroundScheduler()
        scheduler.add_job(decay_scores, IntervalTrigger(hours=1))
        scheduler.add_job(cleanup_auth_events, IntervalTrigger(hours=24))
        scheduler.start()
        app.scheduler = scheduler

    if not app.debug:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/crunevo.log", maxBytes=10240, backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("CRUNEVO startup")
        app.logger.info("Debug=%s", app.debug)
        app.logger.info("DB=%s", app.config.get("SQLALCHEMY_DATABASE_URI"))

    return app
