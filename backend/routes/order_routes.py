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

    order_items = []
    total_amount = 0
    for item in cart_items:
        total_amount += item["price"] * item["quantity"]
        order_items.append({
            "product_id": item["product_id"],
            "product_name": item["product_name"],
            "price": item["price"],
            "quantity": item["quantity"],
            "size": item.get("size"),
            "color": item.get("color"),
        })

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
    # TODO (Phase 9): restrict this to admin users (check request.user_role == "admin")
    data = request.get_json() or {}
    new_status = data.get("status")
    if new_status not in ALLOWED_STATUSES:
        return jsonify({"error": f"status must be one of {ALLOWED_STATUSES}"}), 400

    db = current_app.db
    try:
        result = db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": new_status}})
    except InvalidId:
        return jsonify({"error": "Invalid order id"}), 400
    if result.matched_count == 0:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"message": "Order status updated"})