from flask import Blueprint, current_app, jsonify
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