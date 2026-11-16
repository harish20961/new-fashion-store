from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, current_app, jsonify, request
from utils.auth import admin_required


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard():

    db = current_app.db

    # Dashboard statistics
    total_users = db.users.count_documents({})
    total_products = db.products.count_documents({})
    total_orders = db.orders.count_documents({})

    # Get latest 5 orders
    recent_orders = list(
        db.orders.find()
        .sort("created_at", -1)
        .limit(5)
    )

    orders = []

    for order in recent_orders:

        orders.append({
            "order_id": str(order["_id"]),
            "user_id": order.get("user_id"),
            "total_amount": order.get("total_amount", 0),
            "status": order.get("status", "Placed"),
            "created_at": (
                order["created_at"].isoformat()
                if order.get("created_at")
                else None
            )
        })

    return jsonify({
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "recent_orders": orders
    })


def _iso(value):
    return value.isoformat() if value else None


def _users_by_id(db, id_strings):
    """{user_id_string: user_doc} for a set of id strings (skips bad ids)."""
    ids = []
    for s in set(id_strings):
        try:
            ids.append(ObjectId(s))
        except (InvalidId, TypeError):
            pass
    return {str(u["_id"]): u for u in db.users.find({"_id": {"$in": ids}}, {"password": 0})}


@admin_bp.route("/orders", methods=["GET"])
@admin_required
def list_all_orders():
    db = current_app.db
    query = {}
    status = request.args.get("status")
    if status:
        query["status"] = status

    orders = list(db.orders.find(query).sort("created_at", -1).limit(300))
    users = _users_by_id(db, [o.get("user_id") for o in orders])

    result = []
    for o in orders:
        customer = users.get(o.get("user_id")) or {}
        address = o.get("delivery_address") or {}
        result.append({
            "order_id": str(o["_id"]),
            "customer_name": address.get("full_name") or customer.get("name") or "-",
            "customer_contact": address.get("phone") or customer.get("phone") or customer.get("email") or "-",
            "address": address,
            "items": [
                {"name": i.get("product_name"), "quantity": i.get("quantity"),
                 "size": i.get("size"), "color": i.get("color")}
                for i in o.get("items", [])
            ],
            "total_amount": o.get("total_amount", 0),
            "status": o.get("status", "Placed"),
            "created_at": _iso(o.get("created_at")),
        })
    return jsonify(result)


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    db = current_app.db
    order_counts = {
        row["_id"]: row["count"]
        for row in db.orders.aggregate([{"$group": {"_id": "$user_id", "count": {"$sum": 1}}}])
    }
    users = list(db.users.find({}, {"password": 0}).sort("created_at", -1).limit(500))
    return jsonify([{
        "user_id": str(u["_id"]),
        "name": u.get("name", "-"),
        "email": u.get("email"),
        "phone": u.get("phone"),
        "role": u.get("role", "customer"),
        "orders": order_counts.get(str(u["_id"]), 0),
        "created_at": _iso(u.get("created_at")),
    } for u in users])


@admin_bp.route("/reviews", methods=["GET"])
@admin_required
def list_all_reviews():
    db = current_app.db
    reviews = list(db.reviews.find().sort("created_at", -1).limit(300))

    product_ids = []
    for r in reviews:
        try:
            product_ids.append(ObjectId(r.get("product_id")))
        except (InvalidId, TypeError):
            pass
    products = {str(p["_id"]): p.get("name", "-")
                for p in db.products.find({"_id": {"$in": product_ids}}, {"name": 1})}

    return jsonify([{
        "review_id": str(r["_id"]),
        "product_name": products.get(r.get("product_id"), "(deleted product)"),
        "reviewer_name": r.get("reviewer_name", "-"),
        "rating": r.get("rating"),
        "comment": r.get("comment", ""),
        "created_at": _iso(r.get("created_at")),
    } for r in reviews])


@admin_bp.route("/reviews/<review_id>", methods=["DELETE"])
@admin_required
def delete_review(review_id):
    try:
        result = current_app.db.reviews.delete_one({"_id": ObjectId(review_id)})
    except InvalidId:
        return jsonify({"error": "Invalid review id"}), 400
    if result.deleted_count == 0:
        return jsonify({"error": "Review not found"}), 404
    return jsonify({"message": "Review deleted"})
