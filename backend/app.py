import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import ASCENDING, MongoClient

from config import Config
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.cart_routes import cart_bp
from routes.wishlist_routes import wishlist_bp
from routes.order_routes import order_bp
from routes.review_routes import review_bp
from routes.admin_routes import admin_bp

# frontend/ sits next to backend/ (both locally and inside the Docker image)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


def ensure_indexes(db, logger):
    """Creates the indexes the app relies on. Safe to run on every start."""
    try:
        db.users.create_index("email", unique=True)
        db.products.create_index("category")
        db.carts.create_index("user_id")
        db.orders.create_index([("user_id", ASCENDING), ("created_at", -1)])
        db.reviews.create_index([("product_id", ASCENDING), ("created_at", -1)])
        db.wishlists.create_index("user_id")
    except Exception:
        # e.g. DB unreachable at boot, or old duplicate emails blocking the unique index
        logger.exception("Could not create MongoDB indexes (app will still start)")


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)

    # --- Refuse to start in production with a weak/missing secret ---
    if not app.config["IS_DEV"] and len(app.config["SECRET_KEY"]) < 32:
        raise RuntimeError(
            "SECRET_KEY must be set to a random string of 32+ characters in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # --- CORS: only needed if the frontend is hosted on a different domain ---
    origins = app.config["CORS_ORIGINS"] or (["*"] if app.config["IS_DEV"] else [])
    if origins:
        CORS(app, resources={r"/api/*": {"origins": origins}})

    # --- MongoDB connection ---
    client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=5000)
    app.db = client.get_default_database(default=app.config["MONGO_DB_NAME"])
    ensure_indexes(app.db, app.logger)

    # --- Register route blueprints ---
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(product_bp, url_prefix="/api/products")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(wishlist_bp, url_prefix="/api/wishlist")
    app.register_blueprint(order_bp, url_prefix="/api/orders")
    app.register_blueprint(review_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.route("/api/health")
    def health_check():
        """Quick check that the API is up and MongoDB is reachable."""
        try:
            app.db.command("ping")
            db_status = "connected"
            status_code = 200
        except Exception:
            app.logger.exception("MongoDB health check failed")
            db_status = "disconnected"
            status_code = 503
        response = {"status": "ok" if status_code == 200 else "error", "database": db_status}
        return jsonify(response), status_code

    # --- Serve the storefront + admin panel from the same server (one deploy) ---
    if os.path.isdir(FRONTEND_DIR):
        @app.route("/")
        def home():
            return send_from_directory(FRONTEND_DIR, "index.html")

        @app.route("/<path:filename>")
        def frontend_files(filename):
            if filename.startswith("api/"):
                return jsonify({"error": "Not found"}), 404
            return send_from_directory(FRONTEND_DIR, filename)

    return app


# Production: gunicorn "app:create_app()"   |   Local development: python app.py
if __name__ == "__main__":
    app = create_app()
    app.run(debug=app.config["IS_DEV"], port=int(os.environ.get("PORT", 5000)))
