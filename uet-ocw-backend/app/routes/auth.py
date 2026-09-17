from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.services.authz import current_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

DEFAULT_ROLE_DESCRIPTIONS = {
    "ADMIN": "Full access to all OCW management APIs",
    "TEACHER": "Can apply to teach courses and manage resources for approved courses",
    "STUDENT": "Can apply for courses and view resources after approval",
}


@auth_bp.route("/health", methods=["GET"])
def auth_health():
    return jsonify({
        "status": "success",
        "message": "Auth API is working"
    })


@auth_bp.route("/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)
    unknown_fields = set(payload) - {"username", "email", "password", "role", "role_id", "full_name"}
    if unknown_fields:
        return _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    required_fields = ["username", "email", "password"]
    for field in required_fields:
        if field not in payload:
            return _error(f"{field} is required", 400)

    role, error = _role_from_payload(payload)
    if error:
        return error

    user = User(
        role_id=role.id,
        username=payload["username"].strip(),
        email=payload["email"].strip(),
        password_hash=generate_password_hash(payload["password"]),
        full_name=payload.get("full_name"),
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Username or email already exists", 409)

    token = create_access_token(identity=str(user.id))
    return jsonify({"status": "success", "access_token": token, "data": _serialize_user(user)}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)
    unknown_fields = set(payload) - {"email", "username", "password"}
    if unknown_fields:
        return _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    login_value = payload.get("email") or payload.get("username")
    password = payload.get("password")
    if not isinstance(login_value, str) or not login_value.strip():
        return _error("email or username is required", 400)
    if not isinstance(password, str) or not password:
        return _error("password is required", 400)

    user = db.session.scalar(
        select(User).where((User.email == login_value.strip()) | (User.username == login_value.strip()))
    )
    if user is None or not check_password_hash(user.password_hash, password):
        return _error("Invalid email/username or password", 401)
    if not user.is_active:
        return _error("User account is inactive", 403)

    user.last_login = datetime.utcnow()
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"status": "success", "access_token": token, "data": _serialize_user(user)})


@auth_bp.route("/me", methods=["GET"])
def me():
    user = current_user()
    if user is None:
        return _error("Authentication required", 401)
    return jsonify({"status": "success", "data": _serialize_user(user)})


def _role_from_payload(payload):
    role_id = payload.get("role_id")
    role_name = payload.get("role")

    if role_id is not None:
        if not isinstance(role_id, int) or role_id <= 0:
            return None, _error("role_id must be a positive integer", 400)
        role = db.session.get(Role, role_id)
    else:
        role_name = role_name or "STUDENT"
        if not isinstance(role_name, str) or not role_name.strip():
            return None, _error("role must be a non-empty string", 400)
        role = db.session.scalar(select(Role).where(Role.name == role_name.strip().upper()))

    if role is None:
        if role_name and role_name.strip().upper() in DEFAULT_ROLE_DESCRIPTIONS:
            normalized_role = role_name.strip().upper()
            role = Role(name=normalized_role, description=DEFAULT_ROLE_DESCRIPTIONS[normalized_role])
            db.session.add(role)
            db.session.flush()
        else:
            return None, _error("Role not found. Use role ADMIN, TEACHER, or STUDENT", 404)
    logged_in_user = current_user()
    logged_in_role = logged_in_user.role.name if logged_in_user and logged_in_user.role else None
    if role.name == "ADMIN" and _admin_exists() and logged_in_role != "ADMIN":
        return None, _error("Only an existing admin can create another admin account", 403)
    return role, None


def _admin_exists():
    return db.session.scalar(
        select(User)
        .join(Role)
        .where(Role.name == "ADMIN")
        .limit(1)
    ) is not None


def _serialize_user(user):
    return {
        "id": user.id,
        "role_id": user.role_id,
        "role": {
            "id": user.role.id,
            "name": user.role.name,
            "description": user.role.description,
        } if user.role else None,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
