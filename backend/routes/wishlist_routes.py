from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, current_app, jsonify, request

from utils.auth import token_required

wishlist_bp = Blueprint("wishlist", __name__)


def serialize_wishlist_item(item):
    item["_id"] = str(item["_id"])
    return item


@wishlist_bp.route("", methods=["GET"])
@token_required
def get_wishlist():
    db = current_app.db
    items = list(db.wishlists.find({"user_id": request.user_id}))
    return jsonify([serialize_wishlist_item(i) for i in items])


@wishlist_bp.route("", methods=["POST"])
@token_required
def add_to_wishlist():
    data = request.get_json() or {}
    if "product_id" not in data:
        return jsonify({"error": "product_id is required"}), 400

    db = current_app.db
    try:
        product = db.products.find_one({"_id": ObjectId(data["product_id"])})
    except InvalidId:
        return jsonify({"error": "Invalid product id"}), 400
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # avoid adding the same product twice
    existing = db.wishlists.find_one(
        {"user_id": request.user_id, "product_id": data["product_id"]}
    )
    if existing:
        return jsonify({"message": "Already in wishlist"}), 200

    wishlist_item = {
        "user_id": request.user_id,
        "product_id": data["product_id"],
        "product_name": product["name"],
        "price": product["price"],
    }
    result = db.wishlists.insert_one(wishlist_item)
    return jsonify({"message": "Added to wishlist", "wishlist_item_id": str(result.inserted_id)}), 201


@wishlist_bp.route("/<item_id>", methods=["DELETE"])
@token_required
def remove_from_wishlist(item_id):
    db = current_app.db
    try:
        result = db.wishlists.delete_one({"_id": ObjectId(item_id), "user_id": request.user_id})
    except InvalidId:
        return jsonify({"error": "Invalid wishlist item id"}), 400
    if result.deleted_count == 0:
        return jsonify({"error": "Wishlist item not found"}), 404
    return jsonify({"message": "Removed from wishlist"})


# TODO (practice this yourself): add a route like
# POST /api/wishlist/<item_id>/move-to-cart that reads the wishlist item,
# inserts it into db.carts (like add_to_cart in cart_routes.py), then
# deletes it from db.wishlists. This is exactly what the blueprint's
# "move items to cart" feature means.