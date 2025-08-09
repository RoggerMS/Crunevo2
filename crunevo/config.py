import os
import logging
from dotenv import load_dotenv
import cloudinary

load_dotenv()


class Config:
    DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    IS_PRODUCTION = FLASK_ENV == "production"

    # Avoid host-matching issues in production
    SERVER_NAME = None if IS_PRODUCTION else os.getenv("SERVER_NAME")

    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if DEBUG:
            SECRET_KEY = "devkey"
            logging.getLogger(__name__).warning(
                "SECRET_KEY not set; using insecure default in debug mode"
            )
        else:
            SECRET_KEY = os.urandom(24)
            logging.getLogger(__name__).warning(
                "SECRET_KEY not set; using temporary random value"
            )

    # Secure session cookies in production, allow HTTP in development
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    SESSION_COOKIE_SAMESITE = "Lax"

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///data.db").replace(
        "postgres://", "postgresql://"
    )
    if DEBUG:
        logging.getLogger(__name__).debug("DB: %s", SQLALCHEMY_DATABASE_URI)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
    INVOICE_FOLDER = os.getenv("INVOICE_FOLDER", "static/invoices")
    TRANSLATIONS_FOLDER = os.getenv("TRANSLATIONS_FOLDER", "static/translations")
    NOTE_TRANSLATION_LANGS = os.getenv("NOTE_TRANSLATION_LANGS", "en").split(",")

    CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
    if CLOUDINARY_URL:
        cloudinary.config(cloudinary_url=CLOUDINARY_URL)

    FEED_LIKE_W = float(os.getenv("FEED_LIKE_W", 4))
    FEED_DL_W = float(os.getenv("FEED_DL_W", 2))
    FEED_COM_W = float(os.getenv("FEED_COM_W", 1))
    FEED_HALF_LIFE_H = float(os.getenv("FEED_HALF_LIFE_H", 24))

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "noreply@crunevo.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_SENDER", f"Crunevo <{MAIL_USERNAME}>")

    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    IA_ENABLED = os.getenv("IA_ENABLED", "False").lower() in ("1", "true", "yes")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    MAIL_PROVIDER = os.getenv("MAIL_PROVIDER", "smtp")
    USE_RESEND = MAIL_PROVIDER == "resend" or RESEND_API_KEY is not None
    MAIL_SUPPRESS_SEND = (
        not (MAIL_SERVER and MAIL_USERNAME and MAIL_PASSWORD) and not USE_RESEND
    )

    ONBOARDING_TOKEN_EXP_H = int(os.getenv("ONBOARDING_TOKEN_EXP_H", 1))

    ARGON2_TIME_COST = int(os.getenv("ARGON2_TIME_COST", 2))
    ARGON2_MEMORY_COST = int(os.getenv("ARGON2_MEMORY_COST", 102400))
    ARGON2_PARALLELISM = int(os.getenv("ARGON2_PARALLELISM", 8))

    ENABLE_TALISMAN = os.getenv("ENABLE_TALISMAN", "True").lower() in (
        "1",
        "true",
        "yes",
    )
    ENABLE_CSP_OVERRIDE = os.getenv("ENABLE_CSP_OVERRIDE", "False").lower() in (
        "1",
        "true",
        "yes",
    )

    TALISMAN_CSP = {
        "default-src": ["'self'", "https://cdn.jsdelivr.net"],
        "img-src": ["'self'", "data:", "https://res.cloudinary.com"],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://unpkg.com",
            "https://fonts.googleapis.com",
        ],
        "font-src": [
            "'self'",
            "https://fonts.gstatic.com",
        ],
        "script-src": [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://unpkg.com",
        ],
        "connect-src": [
            "'self'",
            "https://res.cloudinary.com",
            "https://api.openai.com",
        ],
        "frame-src": ["'self'", "https://res.cloudinary.com"],
    }

    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI", os.getenv("REDIS_URL", "memory://")
    )

    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://www.crunevo.com")

    TAG_SUGGESTIONS = os.getenv(
        "TAG_SUGGESTIONS",
        "álgebra,resumen,física,historia del Perú",
    ).split(",")

    from crunevo.constants import NOTE_CATEGORIES, ACADEMIC_LEVELS

    NOTE_CATEGORIES = sorted(
        os.getenv(
            "NOTE_CATEGORIES",
            ",".join(NOTE_CATEGORIES),
        ).split(",")
    )

    ACADEMIC_LEVELS = os.getenv(
        "ACADEMIC_LEVELS",
        ",".join(ACADEMIC_LEVELS),
    ).split(",")

    BACKUP_BUCKET = os.getenv("BACKUP_BUCKET")
    BACKUP_PREFIX = os.getenv("BACKUP_PREFIX", "backups")
    BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")

    MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "0").lower() in (
        "1",
        "true",
        "yes",
    )

    POST_RETENTION_DAYS = int(os.getenv("POST_RETENTION_DAYS", 30))

    SENTRY_DSN = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "production")
    SENTRY_TRACES_RATE = float(os.getenv("SENTRY_TRACES_RATE", 0))

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
    DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
    LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
