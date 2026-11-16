"""One-time fix: copy photo paths saved under the old `image` field into `image_url`.

Run from the project's main folder:   python tools/fix_image_field.py
Uses MONGO_URI / MONGO_DB_NAME from your .env, so it fixes whichever database that points to.
"""
import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def fix(db):
    fixed = 0
    for product in db.products.find({"image": {"$exists": True, "$ne": ""}}):
        db.products.update_one(
            {"_id": product["_id"]},
            {"$set": {"image_url": product["image"]}, "$unset": {"image": ""}},
        )
        print(f"  fixed: {product.get('name')}  ->  {product['image']}")
        fixed += 1
    # leftover empty `image` fields are just noise
    db.products.update_many({"image": ""}, {"$unset": {"image": ""}})
    return fixed


if __name__ == "__main__":
    uri = os.environ.get("MONGO_URI")
    if not uri:
        sys.exit("MONGO_URI not found. Run this from the project folder with your .env in place.")
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    db = client.get_default_database(default=os.environ.get("MONGO_DB_NAME", "fashionhub"))
    print(f"Database: {db.name}")
    print(f"Done. {fix(db)} product(s) updated.")
