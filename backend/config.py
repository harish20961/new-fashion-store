import os

from dotenv import load_dotenv

load_dotenv()  # reads variables from a local .env file, if present


def _is_dev():
    return os.environ.get("FLASK_ENV", "production").lower() == "development"


class Config:
    IS_DEV = _is_dev()

    # In production SECRET_KEY is mandatory (checked in app.create_app).
    SECRET_KEY = os.environ.get("SECRET_KEY") or ("dev-secret-key-change-me" if IS_DEV else "")

    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/fashionhub")
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "fashionhub")

    # Comma-separated list of frontend origins allowed to call the API, e.g.
    # CORS_ORIGINS=https://fashionhub.netlify.app
    # Not needed when Flask serves the frontend itself (same origin).
    CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]

    JWT_EXP_DELTA_SECONDS = 60 * 60 * 24  # login tokens last 24 hours
