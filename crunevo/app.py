from flask import Flask, request, redirect, url_for, flash, current_app, g
from flask_login import current_user
import logging
from logging.handlers import RotatingFileHandler
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from .extensions import (
    db,
    login_manager,
    migrate,
    mail,
    csrf,
    limiter,
    talisman,
    socketio,
    oauth,
)
from flask_wtf.csrf import CSRFError

DEFAULT_CSP = {
    "default-src": "'self'",
    "img-src": ["'self'", "data:", "https://res.cloudinary.com"],
    "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
    "font-src": ["'self'", "https://fonts.gstatic.com"],
    "script-src": ["'self'", "'unsafe-inline'"],
    "connect-src": "'self'",
}


def create_app():
    app = Flask(__name__)
    from .config import Config

    app.config.from_object(Config)
    # Re-apply environment overrides after Config class variables load.
    env_db = os.getenv("DATABASE_URL")
    if env_db:
        app.config["SQLALCHEMY_DATABASE_URI"] = env_db.replace(
            "postgres://", "postgresql://"
        )
    env_talisman = os.getenv("ENABLE_TALISMAN")
    if env_talisman is not None:
        app.config["ENABLE_TALISMAN"] = env_talisman.lower() in ("1", "true", "yes")
    env_rlimit = os.getenv("RATELIMIT_STORAGE_URI")
    if env_rlimit:
        app.config["RATELIMIT_STORAGE_URI"] = env_rlimit

    sentry_dsn = app.config.get("SENTRY_DSN")
    if sentry_dsn:
        sentry_logging = LoggingIntegration(
            level=logging.INFO, event_level=logging.ERROR
        )
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration(), sentry_logging],
            environment=app.config.get("SENTRY_ENVIRONMENT"),
            traces_sample_rate=app.config.get("SENTRY_TRACES_RATE", 0),
        )

    @app.context_processor
    def inject_globals():
        from .constants import ACHIEVEMENT_DETAILS
        from .models import Note, Notification, AchievementPopup
        from flask import session

        try:
            latest_sidebar_notes = (
                Note.query.order_by(Note.created_at.desc()).limit(3).all()
                if db.session
                else []
            )
        except Exception:
            latest_sidebar_notes = []

        urgent_count = 0
        new_achievements = []
        if current_user.is_authenticated and current_user.role in [
            "admin",
            "moderator",
        ]:
            try:
                from .models import Report

                counts = {}
                for r in Report.query.filter_by(status="open").all():
                    if r.description.startswith("Post "):
                        try:
                            pid = int(r.description.split()[1].split(":")[0])
                            counts[pid] = counts.get(pid, 0) + 1
                        except Exception:
                            pass
                urgent_count = sum(1 for c in counts.values() if c >= 3)
            except Exception:
                urgent_count = 0

        if current_user.is_authenticated:
            try:
                popups = AchievementPopup.query.filter_by(
                    user_id=current_user.id, shown=False
                ).all()
                if popups:
                    new_achievements = [
                        {
                            "id": p.achievement.id,
                            "code": p.achievement.code,
                            "title": p.achievement.title,
                            "credit_reward": p.achievement.credit_reward,
                        }
                        for p in popups
                        if p.achievement
                    ]
                    session["new_achievements"] = new_achievements
                else:
                    new_achievements = []
                    session.pop("new_achievements", None)
            except Exception:
                new_achievements = []
                session.pop("new_achievements", None)

        return {
            "PUBLIC_BASE_URL": app.config.get("PUBLIC_BASE_URL"),
            "ACHIEVEMENT_DETAILS": ACHIEVEMENT_DETAILS,
            "SIDEBAR_LATEST_NOTES": latest_sidebar_notes,
            "Notification": Notification,
            "current_app": current_app,
            "CART_COUNT": sum(session.get("cart", {}).values()),
            "URGENT_REPORTS": urgent_count,
            "NEW_ACHIEVEMENTS": new_achievements,
        }

    from .utils.helpers import timesince
    from .cache.link_preview import extract_first_url, get_preview

    app.jinja_env.filters["timesince"] = timesince

    def link_preview(text):
        url = extract_first_url(text)
        if not url:
            return None
        return get_preview(url)

    app.jinja_env.filters["link_preview"] = link_preview

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        access_token_url="https://oauth2.googleapis.com/token",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        api_base_url="https://www.googleapis.com/",
        client_kwargs={"scope": "https://www.googleapis.com/auth/drive.readonly"},
    )
    oauth.register(
        name="dropbox",
        client_id=app.config.get("DROPBOX_CLIENT_ID"),
        client_secret=app.config.get("DROPBOX_CLIENT_SECRET"),
        access_token_url="https://api.dropboxapi.com/oauth2/token",
        authorize_url="https://www.dropbox.com/oauth2/authorize",
        api_base_url="https://api.dropboxapi.com/2/",
        client_kwargs={"token_endpoint_auth_method": "client_secret_post"},
    )
    oauth.register(
        name="linkedin",
        client_id=app.config.get("LINKEDIN_CLIENT_ID"),
        client_secret=app.config.get("LINKEDIN_CLIENT_SECRET"),
        access_token_url="https://www.linkedin.com/oauth/v2/accessToken",
        authorize_url="https://www.linkedin.com/oauth/v2/authorization",
        api_base_url="https://api.linkedin.com/v2/",
        client_kwargs={"scope": "r_liteprofile w_member_social"},
    )
    limiter._storage_uri = app.config.get("RATELIMIT_STORAGE_URI")
    limiter.init_app(app)
    if app.config.get("ENABLE_TALISMAN", True):
        csp = app.config.get("TALISMAN_CSP", DEFAULT_CSP)
        if app.config.get("ENABLE_CSP_OVERRIDE"):
            csp = None
        talisman.init_app(
            app,
            content_security_policy=csp,
            force_https=True,
            strict_transport_security=True,
        )
    login_manager.login_view = "auth.login"

    migrate.init_app(app, db)
    socketio.init_app(app)

    @app.before_request
    def record_page_view():
        if (
            request.path.startswith("/static/")
            or request.path in {"/healthz", "/ping"}
            or request.path.startswith("/socket.io")
        ):
            return
        try:
            from .models import PageView

            if not hasattr(g, "page_views"):
                g.page_views = []
            g.page_views.append(PageView(path=request.path))
        except Exception as e:  # pragma: no cover - avoid crashing on log error
            app.logger.error(f"PageView error: {e}")

    testing_env = os.environ.get("PYTEST_CURRENT_TEST") is not None

    @app.after_request
    def commit_page_view(response):
        page_views = getattr(g, "page_views", None)
        if page_views:
            try:
                db.session.add_all(page_views)
                db.session.commit()
            except Exception as e:  # pragma: no cover - avoid crashing on log error
                app.logger.error(f"PageView error: {e}")
                db.session.rollback()
        return response

    # Initialize database if needed (skip during tests)
    with app.app_context():
        if not testing_env:
            try:
                from .utils.db_init import ensure_database_ready

                ensure_database_ready()
            except Exception as e:
                app.logger.error(f"Database initialization error: {e}")

        try:
            from .models import SiteConfig

            cfg = SiteConfig.query.filter_by(key="maintenance_mode").first()
            if cfg:
                app.config["MAINTENANCE_MODE"] = cfg.value == "1"
            cfg = SiteConfig.query.filter_by(key="post_retention_days").first()
            if cfg:
                app.config["POST_RETENTION_DAYS"] = int(cfg.value)
        except Exception as e:  # pragma: no cover - safeguard on startup
            app.logger.error(f"Error loading maintenance flag: {e}")

    from .routes.onboarding_routes import bp as onboarding_bp
    from .routes.auth_routes import auth_bp
    from .routes.notes_routes import notes_bp
    from .routes.feed_routes import (
        feed_bp,
        api_feed,
        view_post,
        like_post,
        comment_post,
        toggle_save,
        donate_post,
    )
    from .routes.course_routes import (
        course_bp,
        list_courses,
        view_course,
        toggle_save_course,
        my_saved_courses,
        api_search_courses,
    )
    from .routes.store_routes import store_bp
    from .routes.chat_routes import chat_bp
    from .routes.search_routes import search_bp
    from .routes.ia_routes import ia_bp
    from .routes.admin_routes import admin_bp
    from .routes.admin_blocker import admin_blocker_bp
    from .routes.admin.email_routes import admin_email_bp
    from .routes.ranking_routes import ranking_bp
    from .routes.notifications_routes import noti_bp
    from .routes.achievement_routes import ach_bp
    from .routes.errors import errors_bp
    from .routes.missions_routes import missions_bp
    from .routes.health_routes import health_bp
    from .routes.maintenance_routes import maintenance_bp
    from .routes.club_routes import club_bp
    from .routes.forum_routes import forum_bp
    from .routes.event_routes import event_bp, list_events
    from .routes.internship_routes import internship_bp
    from .routes.about_routes import about_bp
    from .routes.static_routes import static_bp
    from .routes.saved_routes import saved_bp
    from .routes.dashboard_routes import dashboard_bp
    from .routes.settings_routes import settings_bp
    from .routes.main_routes import main_bp
    from .routes.story_routes import stories_bp
    from .routes.developer_routes import developer_bp
    from .routes.personal_space_routes import personal_space_bp

    is_admin = os.environ.get("ADMIN_INSTANCE") == "1"
    app.config["ADMIN_INSTANCE"] = is_admin

    app.register_blueprint(health_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(developer_bp)
    app.logger.info("Running in ADMIN mode" if is_admin else "Running in PUBLIC mode")

    if is_admin:
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp)
        app.register_blueprint(admin_email_bp)
    else:
        app.register_blueprint(onboarding_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(notes_bp)
        app.register_blueprint(feed_bp)
        app.register_blueprint(stories_bp)
        app.add_url_rule(
            "/api/feed",
            endpoint="feed.api_feed_alias",
            view_func=api_feed,
        )
        app.add_url_rule(
            "/post/<int:post_id>",
            endpoint="feed.view_post",
            view_func=view_post,
        )
        app.add_url_rule(
            "/posts/<int:post_id>",
            endpoint="feed.view_post_alias",
            view_func=view_post,
        )
        app.add_url_rule(
            "/like/<int:post_id>",
            endpoint="feed.like_post",
            view_func=like_post,
            methods=["POST"],
        )
        app.add_url_rule(
            "/comment/<int:post_id>",
            endpoint="feed.comment_post",
            view_func=comment_post,
            methods=["POST"],
        )
        app.add_url_rule(
            "/save/<int:post_id>",
            endpoint="feed.toggle_save",
            view_func=toggle_save,
            methods=["POST"],
        )
        app.add_url_rule(
            "/donate/<int:post_id>",
            endpoint="feed.donate_post",
            view_func=donate_post,
            methods=["POST"],
        )
        app.register_blueprint(course_bp)
        app.add_url_rule(
            "/courses",
            endpoint="courses.list_courses_alias",
            view_func=list_courses,
        )
        app.add_url_rule(
            "/courses/<int:course_id>",
            endpoint="courses.view_course_alias",
            view_func=view_course,
        )
        app.add_url_rule(
            "/courses/save/<int:course_id>",
            endpoint="courses.toggle_save_course_alias",
            view_func=toggle_save_course,
            methods=["POST"],
        )
        app.add_url_rule(
            "/courses/mis-cursos",
            endpoint="courses.my_saved_courses_alias",
            view_func=my_saved_courses,
        )
        app.add_url_rule(
            "/courses/api/search",
            endpoint="courses.api_search_courses_alias",
            view_func=api_search_courses,
        )
        app.register_blueprint(store_bp)
        app.register_blueprint(chat_bp)
        app.register_blueprint(search_bp)
        app.register_blueprint(ia_bp)
        app.register_blueprint(noti_bp)
        app.register_blueprint(ach_bp)
        app.register_blueprint(missions_bp)
        app.register_blueprint(ranking_bp)
        app.register_blueprint(club_bp)
        app.register_blueprint(forum_bp)
        app.register_blueprint(event_bp)
        app.register_blueprint(internship_bp)
        app.add_url_rule(
            "/events",
            endpoint="event.list_events_alias",
            view_func=list_events,
        )
        app.register_blueprint(about_bp)
        app.register_blueprint(static_bp)
        app.register_blueprint(saved_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(settings_bp)
        app.register_blueprint(personal_space_bp)
        if testing_env:
            app.register_blueprint(admin_bp)
            app.register_blueprint(admin_email_bp)
        app.register_blueprint(admin_blocker_bp)

    app.register_blueprint(errors_bp)

    # Initialize socket namespaces
    import crunevo.routes.socket_routes  # noqa: F401

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash("La sesión expiró, vuelve a intentarlo.", "danger")
        return redirect(request.referrer or url_for("feed.feed_home")), 302

    if os.getenv("SCHEDULER") == "1":
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from .jobs.decay import decay_scores
        from .jobs.cleanup_auth_events import cleanup_auth_events
        from .jobs.backup_db import backup_database
        from .jobs.cleanup_stories import cleanup_stories
        from .jobs.cleanup_inactive_posts import cleanup_inactive_posts

        scheduler = BackgroundScheduler()
        scheduler.add_job(decay_scores, IntervalTrigger(hours=1))
        scheduler.add_job(cleanup_auth_events, IntervalTrigger(hours=24))
        scheduler.add_job(backup_database, IntervalTrigger(weeks=1))
        scheduler.add_job(cleanup_stories, IntervalTrigger(hours=1))
        scheduler.add_job(cleanup_inactive_posts, IntervalTrigger(hours=24))
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