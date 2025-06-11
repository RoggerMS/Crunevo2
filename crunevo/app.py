from flask import Flask
from flask_migrate import Migrate

from .extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    from .config import Config
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .models import User, Product, Note, Comment

    Migrate(app, db)

    # ⚠️ IMPORTANTE: Este decorador debe estar dentro de create_app y usar 'app' local
    @app.before_request
    def create_tables_once():
        if not hasattr(app, 'tables_created'):
            db.create_all()
            if not User.query.first():
                admin = User(username="admin", email="admin@example.com", role="admin")
                admin.set_password("admin")
                user = User(username="estudiante", email="user@example.com")
                user.set_password("test")
                db.session.add_all([admin, user])
                db.session.add(Product(
                    name="Libro de matemáticas",
                    description="Libro PDF",
                    price=9.99,
                    image="https://via.placeholder.com/150",
                    stock=10
                ))
                note = Note(
                    title="Apunte de prueba",
                    description="Introducción",
                    filename="static/uploads/demo.pdf",
                    author=user
                )
                db.session.add(note)
                db.session.add(Comment(body="Muy útil", author=admin, note=note))
                db.session.commit()
            app.tables_created = True

    from .routes.auth_routes import auth_bp
    from .routes.notes_routes import notes_bp
    from .routes.feed_routes import feed_bp
    from .routes.store_routes import store_bp
    from .routes.chat_routes import chat_bp
    from .routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
