import os
from dotenv import load_dotenv
import cloudinary

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "devkey")

    _db_uri = os.getenv("DATABASE_URL", "sqlite:///crunevo.db")
    if _db_uri.startswith("postgres://"):
        _db_uri = _db_uri.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_uri

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")

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
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_SENDER", "Crunevo <no-reply@crunevo.io>")

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
