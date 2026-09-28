import datetime

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, current_app, jsonify, request

from utils.auth import token_required

review_bp = Blueprint("reviews", __name__)


def serialize_review(review):
    review["_id"] = str(review["_id"])
    return review


@review_bp.route("/reviews", methods=["POST"])
@token_required
def create_review():
    data = request.get_json() or {}
    product_id = data.get("product_id")
    rating = data.get("rating")
    comment = data.get("comment", "")

    if not product_id or rating is None:
        return jsonify({"error": "product_id and rating are required"}), 400
    if not isinstance(rating, (int, float)) or not (1 <= rating <= 5):
        return jsonify({"error": "rating must be a number between 1 and 5"}), 400

    db = current_app.db
    try:
        product = db.products.find_one({"_id": ObjectId(product_id)})
    except InvalidId:
        return jsonify({"error": "Invalid product id"}), 400
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # TODO (blueprint requirement): restrict reviews to customers who
    # actually purchased the product — check db.orders for a matching
    # user_id + product_id before allowing this.

    existing = db.reviews.find_one({"user_id": request.user_id, "product_id": product_id})
    if existing:
        return jsonify({"error": "You have already reviewed this product"}), 409

    user = db.users.find_one({"_id": ObjectId(request.user_id)})

    review = {
        "user_id": request.user_id,
        "reviewer_name": user["name"] if user else "Anonymous",
        "product_id": product_id,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.datetime.utcnow(),
    }
    result = db.reviews.insert_one(review)
    return jsonify({"message": "Review added", "review_id": str(result.inserted_id)}), 201


@review_bp.route("/products/<product_id>/reviews", methods=["GET"])
def get_product_reviews(product_id):
    # public route — no login needed to read reviews
    db = current_app.db
    reviews = list(db.reviews.find({"product_id": product_id}).sort("created_at", -1))
    return jsonify([serialize_review(r) for r in reviews])


@review_bp.route("/reviews/<review_id>", methods=["PUT"])
@token_required
def update_review(review_id):
    data = request.get_json() or {}
    updates = {}
    if "rating" in data:
        if not isinstance(data["rating"], (int, float)) or not (1 <= data["rating"] <= 5):
            return jsonify({"error": "rating must be a number between 1 and 5"}), 400
        updates["rating"] = data["rating"]
    if "comment" in data:
        updates["comment"] = data["comment"]

    db = current_app.db
    try:
        result = db.reviews.update_one(
            {"_id": ObjectId(review_id), "user_id": request.user_id}, {"$set": updates}
        )
    except InvalidId:
        return jsonify({"error": "Invalid review id"}), 400
    if result.matched_count == 0:
        return jsonify({"error": "Review not found, or it isn't yours to edit"}), 404
    return jsonify({"message": "Review updated"})


@review_bp.route("/reviews/<review_id>", methods=["DELETE"])
@token_required
def delete_review(review_id):
    db = current_app.db
    try:
        result = db.reviews.delete_one({"_id": ObjectId(review_id), "user_id": request.user_id})
    except InvalidId:
        return jsonify({"error": "Invalid review id"}), 400
    if result.deleted_count == 0:
        return jsonify({"error": "Review not found, or it isn't yours to delete"}), 404
    return jsonify({"message": "Review deleted"})