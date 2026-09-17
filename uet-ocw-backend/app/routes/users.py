import secrets
import string

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.services.authz import ADMIN, require_roles


users_bp = Blueprint("users", __name__, url_prefix="/api/users")

DEFAULT_ROLE_DESCRIPTIONS = {
    "ADMIN": "Full access to all OCW management APIs",
    "TEACHER": "Can apply to teach courses and manage resources for approved courses",
    "STUDENT": "Can apply for courses and view resources after approval",
}


@users_bp.route("", methods=["GET"])
@require_roles(ADMIN)
def get_users():
    try:
        users = db.session.scalars(select(User).order_by(User.id)).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({"status": "success", "data": [_serialize_user(user) for user in users]})


@users_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_user():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)
    unknown_fields = set(payload) - {"username", "email", "password", "role", "role_id", "full_name", "generate_password"}
    if unknown_fields:
        return _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    required_fields = ["username", "email"]
    for field in required_fields:
        if field not in payload:
            return _error(f"{field} is required", 400)

    password = payload.get("password")
    generated_password = None
    if payload.get("generate_password") or not password:
        generated_password = _generate_password()
        password = generated_password
    if not isinstance(password, str) or len(password) < 8:
        return _error("password must be at least 8 characters", 400)

    role, error = _role_from_payload(payload)
    if error:
        return error

    user = User(
        role_id=role.id,
        username=payload["username"].strip(),
        email=payload["email"].strip(),
        password_hash=generate_password_hash(password),
        full_name=payload.get("full_name"),
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Username or email already exists", 409)

    response = {"status": "success", "data": _serialize_user(user)}
    if generated_password:
        response["temporary_password"] = generated_password
    return jsonify(response), 201


@users_bp.route("/<int:user_id>", methods=["GET"])
@require_roles(ADMIN)
def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return _error("User not found", 404)
    return jsonify({"status": "success", "data": _serialize_user(user)})


@users_bp.route("/<int:user_id>/role", methods=["PATCH"])
@require_roles(ADMIN)
def update_user_role(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return _error("User not found", 404)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)

    role_id = payload.get("role_id")
    if not isinstance(role_id, int) or role_id <= 0:
        return _error("role_id must be a positive integer", 400)
    if db.session.get(Role, role_id) is None:
        return _error("Role not found", 404)

    user.role_id = role_id
    db.session.commit()
    return jsonify({"status": "success", "data": _serialize_user(user)})


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


def _role_from_payload(payload):
    role_id = payload.get("role_id")
    name = payload.get("role")

    if role_id is not None:
        if not isinstance(role_id, int) or role_id <= 0:
            return None, _error("role_id must be a positive integer", 400)
        role = db.session.get(Role, role_id)
    else:
        name = name or "STUDENT"
        if not isinstance(name, str) or not name.strip():
            return None, _error("role must be a non-empty string", 400)
        role = db.session.scalar(select(Role).where(Role.name == name.strip().upper()))

    if role is None:
        if name and name.strip().upper() in DEFAULT_ROLE_DESCRIPTIONS:
            role_name = name.strip().upper()
            role = Role(name=role_name, description=DEFAULT_ROLE_DESCRIPTIONS[role_name])
            db.session.add(role)
            db.session.flush()
        else:
            return None, _error("Role not found. Use role ADMIN, TEACHER, or STUDENT", 404)
    return role, None


def _generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
