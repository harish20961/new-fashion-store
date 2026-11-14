from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, current_app, jsonify, request

from utils.auth import token_required

cart_bp = Blueprint("cart", __name__)

MAX_PER_ITEM = 10  # keeps one cart line from being absurdly large


def serialize_cart_item(item):
    item["_id"] = str(item["_id"])
    return item


def available_stock(product):
    """Products created before stock tracking have no stock field; the admin
    panel shows those as 0, so we treat them the same way here."""
    return int(product.get("stock") or 0)


def parse_quantity(value):
    """Returns a positive int, or None if the value isn't one."""
    if isinstance(value, bool):
        return None
    if isinstance(value, float) and not value.is_integer():
        return None
    try:
        quantity = int(value)
    except (TypeError, ValueError):
        return None
    return quantity if quantity >= 1 else None


def validate_options(product, size, color):
    """If a product comes in sizes/colours, the customer has to pick a valid one.
    Returns an error message, or None when everything is fine."""
    sizes = product.get("sizes") or []
    colors = product.get("colors") or []

    if sizes and not size:
        return "Please select a size"
    if sizes and size not in sizes:
        return f"Size {size} isn't available for this product"
    if colors and not color:
        return "Please select a colour"
    if colors and color not in colors:
        return f"{color} isn't available for this product"
    return None


def stock_error(product, wanted, in_cart=0):
    """Checks `wanted` against stock. `in_cart` is what's already in the cart
    for the same variant. Returns (message, left_to_add) or None if fine."""
    stock = available_stock(product)
    if stock <= 0:
        return f"{product['name']} is out of stock", 0
    limit = min(stock, MAX_PER_ITEM)
    if wanted > limit:
        left = max(limit - in_cart, 0)
        if stock > MAX_PER_ITEM:
            return f"You can buy up to {MAX_PER_ITEM} of one item per order", left
        if in_cart:
            return f"Only {stock} in stock — you already have {in_cart} in your cart", left
        return f"Only {stock} in stock", left
    return None


@cart_bp.route("", methods=["GET"])
@token_required
def get_cart():
    db = current_app.db
    items = list(db.carts.find({"user_id": request.user_id}))

    # one query for all the products, so the cart can show live stock + images
    ids = []
    for item in items:
        try:
            ids.append(ObjectId(item["product_id"]))
        except (InvalidId, TypeError):
            pass
    products = {str(p["_id"]): p for p in db.products.find({"_id": {"$in": ids}})}

    result = []
    for item in items:
        product = products.get(item["product_id"])
        item = serialize_cart_item(item)
        if product:
            item["stock"] = available_stock(product)
            item["image_url"] = product.get("image_url")
            item["price"] = product["price"]  # always show the current price
            item["unavailable"] = False
        else:
            item["stock"] = 0
            item["unavailable"] = True
        result.append(item)
    return jsonify(result)


@cart_bp.route("", methods=["POST"])
@token_required
def add_to_cart():
    data = request.get_json() or {}
    if "product_id" not in data:
        return jsonify({"error": "product_id is required"}), 400

    quantity = parse_quantity(data.get("quantity", 1))
    if quantity is None:
        return jsonify({"error": "quantity must be a whole number of 1 or more"}), 400

    db = current_app.db
    try:
        product = db.products.find_one({"_id": ObjectId(data["product_id"])})
    except InvalidId:
        return jsonify({"error": "Invalid product id"}), 400
    if not product:
        return jsonify({"error": "Product not found"}), 404

    size = data.get("size") or None
    color = data.get("color") or None
    option_error = validate_options(product, size, color)
    if option_error:
        return jsonify({"error": option_error}), 400

    # same product + size + colour already in the cart? then add to that line
    variant = {
        "user_id": request.user_id,
        "product_id": data["product_id"],
        "size": size,
        "color": color,
    }
    existing = db.carts.find_one(variant)
    in_cart = existing["quantity"] if existing else 0

    problem = stock_error(product, in_cart + quantity, in_cart)
    if problem:
        message, left = problem
        return jsonify({"error": message, "available": left}), 409

    if existing:
        db.carts.update_one({"_id": existing["_id"]}, {"$inc": {"quantity": quantity}})
        return jsonify({"message": "Cart updated", "cart_item_id": str(existing["_id"])}), 200

    cart_item = {
        **variant,
        "product_name": product["name"],
        "price": product["price"],
        "quantity": quantity,
    }
    result = db.carts.insert_one(cart_item)
    return jsonify({"message": "Added to cart", "cart_item_id": str(result.inserted_id)}), 201


@cart_bp.route("/<item_id>", methods=["PUT"])
@token_required
def update_cart_item(item_id):
    data = request.get_json() or {}
    db = current_app.db

    try:
        item = db.carts.find_one({"_id": ObjectId(item_id), "user_id": request.user_id})
    except InvalidId:
        return jsonify({"error": "Invalid cart item id"}), 400
    if not item:
        return jsonify({"error": "Cart item not found"}), 404

    product = db.products.find_one({"_id": ObjectId(item["product_id"])})
    if not product:
        return jsonify({"error": "This product is no longer available"}), 404

    updates = {}

    if "quantity" in data:
        quantity = parse_quantity(data["quantity"])
        if quantity is None:
            return jsonify({"error": "quantity must be a whole number of 1 or more"}), 400
        problem = stock_error(product, quantity)
        if problem:
            return jsonify({"error": problem[0], "available": min(available_stock(product), MAX_PER_ITEM)}), 409
        updates["quantity"] = quantity

    if "size" in data or "color" in data:
        size = data.get("size", item.get("size"))
        color = data.get("color", item.get("color"))
        option_error = validate_options(product, size, color)
        if option_error:
            return jsonify({"error": option_error}), 400
        updates["size"] = size
        updates["color"] = color

    if not updates:
        return jsonify({"error": "Nothing to update"}), 400

    db.carts.update_one({"_id": item["_id"]}, {"$set": updates})
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
