from .feed import feed_api_bp
from .notes import notes_api_bp
from .users import users_api_bp


def init_api(app):
    app.register_blueprint(feed_api_bp)
    app.register_blueprint(notes_api_bp)
    app.register_blueprint(users_api_bp)
