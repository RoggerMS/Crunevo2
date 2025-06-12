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
