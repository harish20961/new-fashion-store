from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, current_app, jsonify, request

from utils.auth import token_required

cart_bp = Blueprint("cart", __name__)


def serialize_cart_item(item):
    item["_id"] = str(item["_id"])
    return item


@cart_bp.route("", methods=["GET"])
@token_required
def get_cart():
    db = current_app.db
    items = list(db.carts.find({"user_id": request.user_id}))
    return jsonify([serialize_cart_item(i) for i in items])


@cart_bp.route("", methods=["POST"])
@token_required
def add_to_cart():
    data = request.get_json() or {}
    if "product_id" not in data or "quantity" not in data:
        return jsonify({"error": "product_id and quantity are required"}), 400

    db = current_app.db
    try:
        product = db.products.find_one({"_id": ObjectId(data["product_id"])})
    except InvalidId:
        return jsonify({"error": "Invalid product id"}), 400
    if not product:
        return jsonify({"error": "Product not found"}), 404

    cart_item = {
        "user_id": request.user_id,
        "product_id": data["product_id"],
        "product_name": product["name"],
        "price": product["price"],
        "quantity": data["quantity"],
        "size": data.get("size"),
        "color": data.get("color"),
    }
    result = db.carts.insert_one(cart_item)
    return jsonify({"message": "Added to cart", "cart_item_id": str(result.inserted_id)}), 201


@cart_bp.route("/<item_id>", methods=["PUT"])
@token_required
def update_cart_item(item_id):
    data = request.get_json() or {}
    updates = {k: v for k, v in data.items() if k in ("quantity", "size", "color")}
    db = current_app.db
    try:
        result = db.carts.update_one(
            {"_id": ObjectId(item_id), "user_id": request.user_id}, {"$set": updates}
        )
    except InvalidId:
        return jsonify({"error": "Invalid cart item id"}), 400
    if result.matched_count == 0:
        return jsonify({"error": "Cart item not found"}), 404
    return jsonify({"message": "Cart item updated"})


@cart_bp.route("/<item_id>", methods=["DELETE"])
@token_required
def remove_from_cart(item_id):
    db = current_app.db
    try:
        result = db.carts.delete_one({"_id": ObjectId(item_id), "user_id": request.user_id})
    except InvalidId:
        return jsonify({"error": "Invalid cart item id"}), 400
    if result.deleted_count == 0:
        return jsonify({"error": "Cart item not found"}), 404
    return jsonify({"message": "Removed from cart"})