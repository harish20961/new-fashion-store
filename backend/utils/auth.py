from functools import wraps

import jwt
from flask import current_app, jsonify, request


def token_required(f):
    """Checks the Authorization header for a valid JWT and attaches
    request.user_id before running the actual route function."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Missing token"}), 401

        try:
            payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        request.user_id = payload["user_id"]
        request.user_role = payload.get("role", "customer")
        return f(*args, **kwargs)

    return decorated