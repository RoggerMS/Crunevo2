from flask import current_app
from crunevo.extensions import db
import os


def init_database():
    """Initialize database tables if they don't exist."""
    try:
        # Check if tables exist by trying a simple query
        db.session.execute(db.text("SELECT 1 FROM user LIMIT 1"))
        current_app.logger.info("Database tables already exist")
    except Exception as e:
        current_app.logger.info(f"Database tables don't exist or error: {e}")
        try:
            # Create all tables
            db.create_all()
            current_app.logger.info("Database tables created successfully")
        except Exception as create_error:
            current_app.logger.error(
                f"Failed to create database tables: {create_error}"
            )
            raise


def ensure_database_ready():
    """Ensure database is ready and has all required tables."""
    try:
        if not os.path.exists("instance"):
            os.makedirs("instance", exist_ok=True)
        init_database()
        return True
    except Exception as e:
        current_app.logger.error(f"Database initialization failed: {e}")
        return False
