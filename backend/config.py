import os

from dotenv import load_dotenv

load_dotenv()  # reads variables from a local .env file, if present


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Replace with your MongoDB Atlas URI in .env for cloud deployments.
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/fashionhub")
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "fashionhub")

    JWT_EXP_DELTA_SECONDS = 60 * 60 * 24  # login tokens last 24 hours
