from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, current_app, jsonify, request

from utils.auth import admin_required

product_bp = Blueprint("products", __name__)


def serialize_product(product):
    product["_id"] = str(product["_id"])
    return product


@product_bp.route("", methods=["GET"])
def list_products():
    """
    Supports basic filtering + search via query params, e.g.:
    /api/products?category=Men&search=shirt
    Extend this with price range, brand, size, color, sorting etc. (Phase 6).
    """
    db = current_app.db
    query = {}

    category = request.args.get("category")
    if category:
        query["category"] = category

    search = request.args.get("search")
    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    products = list(db.products.find(query).limit(50))
    return jsonify([serialize_product(p) for p in products])


@product_bp.route("/<product_id>", methods=["GET"])
def get_product(product_id):
    db = current_app.db
    try:
        product = db.products.find_one({"_id": ObjectId(product_id)})
    except InvalidId:
        return jsonify({"error": "Invalid product id"}), 400

    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(serialize_product(product))


@product_bp.route("", methods=["POST"])
@admin_required
def create_product():
    # TODO (Phase 9): restrict this route to logged-in admins once
    # role-based access control is added on top of the JWT in auth_routes.py
    data = request.get_json() or {}
    required = ["name", "price", "category"]
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    db = current_app.db
    result = db.products.insert_one(data)
    return jsonify({"message": "Product created", "product_id": str(result.inserted_id)}), 201


@product_bp.route("/<product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):
    # TODO (Phase 9): admin-only
    data = request.get_json() or {}
    db = current_app.db
    try:
        result = db.products.update_one({"_id": ObjectId(product_id)}, {"$set": data})
    except InvalidId:
        return jsonify({"error": "Invalid product id"}), 400

    if result.matched_count == 0:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Product updated"})


@product_bp.route("/<product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):
    # TODO (Phase 9): admin-only
    db = current_app.db
    try:
        result = db.products.delete_one({"_id": ObjectId(product_id)})
    except InvalidId:
        return jsonify({"error": "Invalid product id"}), 400

    if result.deleted_count == 0:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Product deleted"})
