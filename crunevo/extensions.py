from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Centralized extensions so models and blueprints can import `db` and
# `login_manager` without causing circular imports.
db = SQLAlchemy()
login_manager = LoginManager()
