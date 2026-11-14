from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient

from config import Config
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.cart_routes import cart_bp
from routes.wishlist_routes import wishlist_bp
from routes.order_routes import order_bp
from routes.review_routes import review_bp
from routes.admin_routes import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)  # allows the frontend (opened as a separate file/port) to call this API

    # --- MongoDB connection ---
    # Works with a local MongoDB or a MongoDB Atlas connection string (see .env.example)
    client = MongoClient(app.config["MONGO_URI"])
    app.db = client.get_default_database(default=app.config["MONGO_DB_NAME"])

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

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)

