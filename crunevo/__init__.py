
import logging
import os
from datetime import datetime
from flask import Flask, g, request, redirect, url_for, flash
from flask_login import current_user
from werkzeug.exceptions import HTTPException

from crunevo.config import Config
from crunevo.extensions import db, login_manager, migrate, csrf, mail
from crunevo.utils.helpers import activated_required
from crunevo.utils.notify import send_notification


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Configure login manager
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor inicia sesión para acceder a esta página."
    login_manager.login_message_category = "info"

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from crunevo.models import User
        return User.query.get(int(user_id))

    # Before request handlers
    @app.before_request
    def before_request():
        g.start_time = datetime.utcnow()
        
        # Check if user needs activation for protected routes
        if current_user.is_authenticated and not current_user.activated:
            exempt_endpoints = [
                'auth.logout', 'onboarding.pending', 'onboarding.confirm',
                'static', 'main.index', 'auth.login'
            ]
            if request.endpoint not in exempt_endpoints:
                return redirect(url_for('onboarding.pending'))

    # Template globals
    @app.context_processor
    def inject_globals():
        return {
            'current_year': datetime.utcnow().year,
            'app_name': 'CRUNEVO',
            'app_version': '2.0.0'
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(HTTPException)
    def handle_exception(e):
        return render_template('errors/500.html'), 500

    # Register blueprints
    from crunevo.routes.main_routes import main_bp
    from crunevo.routes.auth_routes import auth_bp
    from crunevo.routes.feed_routes import feed_bp
    from crunevo.routes.notes_routes import notes_bp
    from crunevo.routes.forum_routes import forum_bp
    from crunevo.routes.store_routes import store_bp
    from crunevo.routes.admin_routes import admin_bp
    from crunevo.routes.ranking_routes import ranking_bp
    from crunevo.routes.achievement_routes import ach_bp as achievement_bp
    from crunevo.routes.missions_routes import missions_bp
    from crunevo.routes.notifications_routes import notifications_bp
    from crunevo.routes.onboarding_routes import onboarding_bp
    from crunevo.routes.about_routes import about_bp
    from crunevo.routes.ia_routes import ia_bp
    from crunevo.routes.health_routes import health_bp
    from crunevo.routes.static_routes import static_bp
    from crunevo.routes.certificate_routes import certificate_bp
    from crunevo.routes.saved_routes import saved_bp
    from crunevo.routes.event_routes import event_bp
    from crunevo.routes.course_routes import course_bp
    from crunevo.routes.club_routes import club_bp
    from crunevo.routes.chat_routes import chat_bp
    from crunevo.routes.crunebot_routes import crunebot_bp
    from crunevo.routes.search_routes import search_bp

    # Register all blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(notes_bp, url_prefix='/notes')
    app.register_blueprint(forum_bp, url_prefix='/forum')
    app.register_blueprint(store_bp, url_prefix='/store')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ranking_bp, url_prefix='/ranking')
    app.register_blueprint(achievement_bp, url_prefix='/achievements')
    app.register_blueprint(missions_bp, url_prefix='/misiones')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(onboarding_bp, url_prefix='/onboarding')
    app.register_blueprint(about_bp, url_prefix='/about')
    app.register_blueprint(ia_bp, url_prefix='/ia')
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(static_bp, url_prefix='/legal')
    app.register_blueprint(certificate_bp, url_prefix='/certificates')
    app.register_blueprint(saved_bp, url_prefix='/saved')
    app.register_blueprint(event_bp, url_prefix='/events')
    app.register_blueprint(course_bp, url_prefix='/courses')
    app.register_blueprint(club_bp, url_prefix='/clubes')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(crunebot_bp)
    app.register_blueprint(search_bp, url_prefix='/search')

    # CLI commands
    @app.cli.command()
    def init_db():
        """Initialize the database."""
        db.create_all()
        print("Database initialized.")

    @app.cli.command()
    def create_admin():
        """Create admin user."""
        from crunevo.models import User
        
        admin = User(
            username='admin',
            email='admin@crunevo.com',
            role='admin',
            activated=True,
            verification_level=3
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")

    # Custom template filters
    @app.template_filter('timeago')
    def timeago_filter(date):
        if not date:
            return ''
        
        now = datetime.utcnow()
        diff = now - date
        
        if diff.days > 0:
            return f"hace {diff.days} día{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"hace {hours} hora{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"hace {minutes} minuto{'s' if minutes > 1 else ''}"
        else:
            return "hace unos segundos"

    @app.template_filter('truncate_smart')
    def truncate_smart_filter(text, length=100):
        if not text or len(text) <= length:
            return text
        return text[:length].rsplit(' ', 1)[0] + '...'

    # Performance monitoring
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = datetime.utcnow() - g.start_time
            if duration.total_seconds() > 1:  # Log slow requests
                app.logger.warning(f"Slow request: {request.endpoint} took {duration.total_seconds():.2f}s")
        return response

    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/crunevo.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('CRUNEVO startup')

    return app


# Import models to ensure they're registered
from crunevo.models import *
