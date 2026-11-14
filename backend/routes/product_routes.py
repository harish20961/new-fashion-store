import re

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, current_app, jsonify, request

from utils.auth import admin_required

product_bp = Blueprint("products", __name__)


def serialize_product(product):
    product["_id"] = str(product["_id"])
    return product


SORT_OPTIONS = {
    "newest": [("_id", -1)],
    "price_asc": [("price", 1), ("_id", -1)],
    "price_desc": [("price", -1), ("_id", -1)],
    "name_asc": [("name", 1)],
}

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


def _to_number(value):
    """Turns a query-string value into a number, or None if it isn't one."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _csv_arg(name):
    """?size=M,L  ->  ["M", "L"]"""
    raw = request.args.get(name, "")
    return [part.strip() for part in raw.split(",") if part.strip()]


@product_bp.route("", methods=["GET"])
def list_products():
    """
    Filtering, search and sorting via query params, e.g.:
    /api/products?category=Men&search=denim&min_price=500&max_price=2500
                 &size=M,L&color=Blue&brand=Urban%20Thread&in_stock=1
                 &sort=price_asc
    Every param is optional and they can be combined.
    """
    db = current_app.db
    query = {}

    category = request.args.get("category")
    if category:
        query["category"] = category

    search = request.args.get("search", "").strip()
    if search:
        # re.escape stops users typing regex characters that break (or abuse) the query
        pattern = {"$regex": re.escape(search), "$options": "i"}
        query["$or"] = [
            {"name": pattern},
            {"brand": pattern},
            {"description": pattern},
            {"category": pattern},
            {"subcategory": pattern},
        ]

    brands = _csv_arg("brand")
    if brands:
        query["brand"] = {"$in": brands}

    sizes = _csv_arg("size")
    if sizes:
        query["sizes"] = {"$in": sizes}

    colors = _csv_arg("color")
    if colors:
        query["colors"] = {"$in": colors}

    price_filter = {}
    min_price = _to_number(request.args.get("min_price"))
    max_price = _to_number(request.args.get("max_price"))
    if min_price is not None:
        price_filter["$gte"] = min_price
    if max_price is not None:
        price_filter["$lte"] = max_price
    if price_filter:
        query["price"] = price_filter

    if request.args.get("in_stock") in ("1", "true", "yes"):
        query["stock"] = {"$gt": 0}

    sort = SORT_OPTIONS.get(request.args.get("sort", "newest"), SORT_OPTIONS["newest"])

    try:
        limit = min(max(int(request.args.get("limit", 100)), 1), 200)
    except ValueError:
        limit = 100

    products = list(db.products.find(query).sort(sort).limit(limit))
    return jsonify([serialize_product(p) for p in products])


@product_bp.route("/filters", methods=["GET"])
def get_filter_options():
    """Returns the values that exist in the catalogue, so the frontend can
    build its filter panel from real data instead of hard-coded lists.
    Pass ?category=Men to get only the sizes/colours/brands used in that category
    (so shoppers browsing Men don't see shoe sizes, for example)."""
    db = current_app.db
    category = request.args.get("category")
    scope = {"category": category} if category else {}

    def clean(values):
        return sorted({v for v in values if v})

    sizes = clean(db.products.distinct("sizes", scope))
    sizes.sort(key=lambda s: (SIZE_ORDER.index(s) if s in SIZE_ORDER else 99,
                              int(s) if str(s).isdigit() else 0, str(s)))

    cheapest = db.products.find_one(scope, sort=[("price", 1)])
    priciest = db.products.find_one(scope, sort=[("price", -1)])

    return jsonify({
        # categories always lists everything, so the dropdown never shrinks
        "categories": clean(db.products.distinct("category")),
        "brands": clean(db.products.distinct("brand", scope)),
        "sizes": sizes,
        "colors": clean(db.products.distinct("colors", scope)),
        "min_price": cheapest["price"] if cheapest else 0,
        "max_price": priciest["price"] if priciest else 0,
    })


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
