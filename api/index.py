import os
import sys

# Set environment variables for serverless compatibility
os.environ.setdefault("FLASK_ENV", "production")
os.environ.setdefault("ENABLE_TALISMAN", "False")  # Disable Talisman in serverless
os.environ.setdefault("SCHEDULER", "0")  # Disable scheduler in serverless
os.environ.setdefault("REDIS_URL", "memory://")  # Use memory storage for rate limiting
os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")  # Use memory storage

# Disable eventlet for serverless compatibility
os.environ.setdefault("DISABLE_EVENTLET", "1")

try:
    from crunevo.app import create_app

    app = create_app()
except Exception as e:
    # Create a minimal Flask app for debugging
    from flask import Flask, jsonify

    app = Flask(__name__)
    error_message = str(e)

    @app.route("/")
    def health():
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"App initialization failed: {error_message}",
                    "python_version": sys.version,
                    "environment": dict(os.environ),
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run()
