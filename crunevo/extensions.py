from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Centralized extensions so models and blueprints can import `db`, `migrate` and
# `login_manager` without causing circular imports.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
