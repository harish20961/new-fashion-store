import datetime
import re

import jwt
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from flask import Blueprint, current_app, jsonify, request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Please enter a valid email address"}), 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"error": f"Password must be at least {MIN_PASSWORD_LENGTH} characters"}), 400

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
    try:
        result = db.users.insert_one(user)
    except DuplicateKeyError:
        return jsonify({"error": "An account with this email already exists"}), 409

    return jsonify({"message": "Account created", "user_id": str(result.inserted_id)}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    db = current_app.db
    user = db.users.find_one({"email": email})

    if not user or not user.get("password") or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    payload = {
        "user_id": str(user["_id"]),
        "role": user.get("role", "customer"),
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(seconds=current_app.config["JWT_EXP_DELTA_SECONDS"]),
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    return jsonify({"token": token, "name": user["name"], "role": user.get("role", "customer")})


def _make_token(user):
    payload = {
        "user_id": str(user["_id"]),
        "role": user.get("role", "customer"),
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(seconds=current_app.config["JWT_EXP_DELTA_SECONDS"]),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


@auth_bp.route("/phone-login", methods=["POST"])
def phone_login():
    """Login / signup with a phone number.

    The browser asks Firebase to SMS an OTP and, once the customer enters it,
    gets a Firebase ID token. We never trust the phone number sent by the
    browser: we verify the token's signature with Google and read the phone
    number from inside the token.
    """
    data = request.get_json() or {}
    firebase_token = data.get("id_token") or ""
    name = (data.get("name") or "").strip()[:60]
    if not firebase_token:
        return jsonify({"error": "id_token is required"}), 400

    try:
        claims = google_id_token.verify_firebase_token(
            firebase_token,
            google_requests.Request(),
            audience=current_app.config["FIREBASE_PROJECT_ID"],
        )
    except Exception:
        current_app.logger.exception("Firebase token verification failed")
        claims = None

    if not claims:
        return jsonify({"error": "Could not verify OTP. Please try again."}), 401
    if (claims.get("firebase") or {}).get("sign_in_provider") != "phone":
        return jsonify({"error": "Invalid login method"}), 401
    phone = claims.get("phone_number")
    if not phone:
        return jsonify({"error": "Phone number missing in token"}), 401

    db = current_app.db
    user = db.users.find_one({"phone": phone})
    if not user:
        user = {
            "name": name or f"Customer {phone[-4:]}",
            "phone": phone,
            "role": "customer",
            "created_at": datetime.datetime.utcnow(),
        }
        try:
            user["_id"] = db.users.insert_one(user).inserted_id
        except DuplicateKeyError:  # two quick requests for a new number
            user = db.users.find_one({"phone": phone})

    return jsonify({
        "token": _make_token(user),
        "name": user["name"],
        "role": user.get("role", "customer"),
    })


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
