import os

from dotenv import load_dotenv

load_dotenv()  # reads variables from a local .env file, if present


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Local Mongo default; replace with your MongoDB Atlas connection string
    # (copy .env.example to .env and set MONGO_URI there — never commit .env)
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/fashionhub")

    JWT_EXP_DELTA_SECONDS = 60 * 60 * 24  # login tokens last 24 hours
