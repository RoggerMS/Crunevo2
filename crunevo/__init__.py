"""Application package initializer."""

from .app import create_app as _create_app
from .routes import main_routes, static_routes
import os


def create_app():
    app = _create_app()

    if os.environ.get("ADMIN_INSTANCE") != "1":
        app.register_blueprint(main_routes.main_bp)
        app.register_blueprint(static_routes.static_bp)

    from crunevo.routes.main_routes import main_bp
    from crunevo.routes.auth_routes import auth_bp
    from crunevo.routes.notes_routes import notes_bp
    from crunevo.routes.admin_routes import admin_bp
    from crunevo.routes.store_routes import store_bp
    from crunevo.routes.forum_routes import forum_bp
    from crunevo.routes.notifications_routes import notifications_bp
    from crunevo.routes.health_routes import health_bp
    from crunevo.routes.feed_routes import feed_bp
    from crunevo.routes.saved_routes import saved_bp
    from crunevo.routes.ia_routes import ia_bp
    from crunevo.routes.search_routes import search_bp
    from crunevo.routes.achievement_routes import achievement_bp
    from crunevo.routes.certificate_routes import certificate_bp
    from crunevo.routes.missions_routes import missions_bp
    from crunevo.routes.onboarding_routes import onboarding_bp
    from crunevo.routes.static_routes import static_bp
    from crunevo.routes.about_routes import about_bp
    from crunevo.routes.course_routes import courses_bp
    from crunevo.routes.ranking_routes import ranking_bp
    from crunevo.routes.event_routes import event_bp
    from crunevo.routes.club_routes import club_bp
    from crunevo.routes.chat_routes import chat_bp
    from crunevo.routes.crunebot_routes import crunebot_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(saved_bp, name='saved_content')
    app.register_blueprint(ia_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(achievement_bp)
    app.register_blueprint(certificate_bp)
    app.register_blueprint(missions_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(static_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(ranking_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(club_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(crunebot_bp)

    return app