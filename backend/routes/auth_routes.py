import datetime

import jwt
from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400

    db = current_app.db
    if db.users.find_one({"email": email}):
        return jsonify({"error": "An account with this email already exists"}), 409

    user = {
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "role": "customer",
        "created_at": datetime.datetime.utcnow(),
    }
    result = db.users.insert_one(user)

    return jsonify({"message": "Account created", "user_id": str(result.inserted_id)}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    db = current_app.db
    user = db.users.find_one({"email": email})

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    payload = {
        "user_id": str(user["_id"]),
        "role": user.get("role", "customer"),
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(seconds=current_app.config["JWT_EXP_DELTA_SECONDS"]),
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    return jsonify({"token": token, "name": user["name"], "role": user.get("role", "customer")})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    # JWTs are stateless, so "logout" just means the frontend deletes the
    # stored token. This endpoint exists so the frontend has something to
    # call and so you have a place to add token-blacklisting later if needed.
    return jsonify({"message": "Logged out"})


@auth_bp.route("/me", methods=["GET"])
def me():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return jsonify({"error": "Missing token"}), 401

    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired, please log in again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    db = current_app.db
    user = db.users.find_one({"_id": ObjectId(payload["user_id"])}, {"password": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    user["_id"] = str(user["_id"])
    return jsonify(user)
