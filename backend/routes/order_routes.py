import datetime

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, current_app, jsonify, request

from utils.auth import token_required, admin_required

order_bp = Blueprint("orders", __name__)

ALLOWED_STATUSES = ["Placed", "Processing", "Shipped", "Delivered", "Cancelled"]


def serialize_order(order):
    order["_id"] = str(order["_id"])
    return order


@order_bp.route("", methods=["POST"])
@token_required
def create_order():
    data = request.get_json() or {}
    delivery_address = data.get("delivery_address")
    if not delivery_address:
        return jsonify({"error": "delivery_address is required"}), 400

    db = current_app.db
    cart_items = list(db.carts.find({"user_id": request.user_id}))
    if not cart_items:
        return jsonify({"error": "Your cart is empty"}), 400

    # --- 1. Re-check every item against the live catalogue (price, stock) ---
    order_items = []
    total_amount = 0
    for item in cart_items:
        try:
            product = db.products.find_one({"_id": ObjectId(item["product_id"])})
        except InvalidId:
            product = None
        if not product:
            return jsonify({"error": f"{item['product_name']} is no longer available. Please remove it from your cart."}), 409
        if int(product.get("stock") or 0) < item["quantity"]:
            return jsonify({"error": f"Not enough stock for {product['name']}. Please update your cart."}), 409

        price = product["price"]  # use today's price, not the one saved when added
        total_amount += price * item["quantity"]
        order_items.append({
            "product_id": item["product_id"],
            "product_name": product["name"],
            "price": price,
            "quantity": item["quantity"],
            "size": item.get("size"),
            "color": item.get("color"),
            "image_url": product.get("image_url"),
        })

    # --- 2. Take the stock. The filter {"stock": {"$gte": qty}} makes each
    #        decrement atomic, so two people can't both buy the last item. ---
    reserved = []
    for item in order_items:
        result = db.products.update_one(
            {"_id": ObjectId(item["product_id"]), "stock": {"$gte": item["quantity"]}},
            {"$inc": {"stock": -item["quantity"]}},
        )
        if result.modified_count == 0:
            # someone else bought it a moment ago -> put back what we already took
            for done in reserved:
                db.products.update_one(
                    {"_id": ObjectId(done["product_id"])}, {"$inc": {"stock": done["quantity"]}}
                )
            return jsonify({"error": f"Sorry, {item['product_name']} just sold out. Please update your cart."}), 409
        reserved.append(item)

    order = {
        "user_id": request.user_id,
        "items": order_items,
        "delivery_address": delivery_address,
        "total_amount": total_amount,
        "status": "Placed",
        "created_at": datetime.datetime.utcnow(),
    }
    result = db.orders.insert_one(order)

    # order placed successfully, so empty the cart
    db.carts.delete_many({"user_id": request.user_id})

    return jsonify({
        "message": "Order placed",
        "order_id": str(result.inserted_id),
        "total_amount": total_amount,
    }), 201


@order_bp.route("", methods=["GET"])
@token_required
def list_orders():
    db = current_app.db
    orders = list(db.orders.find({"user_id": request.user_id}).sort("created_at", -1))
    return jsonify([serialize_order(o) for o in orders])


@order_bp.route("/<order_id>", methods=["GET"])
@token_required
def get_order(order_id):
    db = current_app.db
    try:
        order = db.orders.find_one({"_id": ObjectId(order_id), "user_id": request.user_id})
    except InvalidId:
        return jsonify({"error": "Invalid order id"}), 400
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(serialize_order(order))


@order_bp.route("/<order_id>/status", methods=["PUT"])
@admin_required
def update_order_status(order_id):
    data = request.get_json() or {}
    new_status = data.get("status")
    if new_status not in ALLOWED_STATUSES:
        return jsonify({"error": f"status must be one of {ALLOWED_STATUSES}"}), 400

    db = current_app.db
    try:
        order = db.orders.find_one({"_id": ObjectId(order_id)})
    except InvalidId:
        return jsonify({"error": "Invalid order id"}), 400
    if not order:
        return jsonify({"error": "Order not found"}), 404

    db.orders.update_one({"_id": order["_id"]}, {"$set": {"status": new_status}})

    # cancelling an order puts its items back on the shelf (only once)
    if new_status == "Cancelled" and order.get("status") != "Cancelled":
        for item in order.get("items", []):
            try:
                db.products.update_one(
                    {"_id": ObjectId(item["product_id"])}, {"$inc": {"stock": item["quantity"]}}
                )
            except InvalidId:
                pass

    return jsonify({"message": "Order status updated"})
