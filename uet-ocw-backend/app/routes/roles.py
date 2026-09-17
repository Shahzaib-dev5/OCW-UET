from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.role import Role
from app.services.authz import ADMIN, require_roles


roles_bp = Blueprint("roles", __name__, url_prefix="/api/roles")

DEFAULT_ROLES = {
    "ADMIN": "Full access to all OCW management APIs",
    "TEACHER": "Can apply to teach courses and manage resources for approved courses",
    "STUDENT": "Can apply for courses and view resources after approval",
}


@roles_bp.route("", methods=["GET"])
def get_roles():
    try:
        roles = db.session.scalars(select(Role).order_by(Role.id)).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({"status": "success", "data": [_serialize_role(role) for role in roles]})


@roles_bp.route("/seed", methods=["POST"])
def seed_roles():
    for name, description in DEFAULT_ROLES.items():
        role = db.session.scalar(select(Role).where(Role.name == name))
        if role is None:
            db.session.add(Role(name=name, description=description))
        else:
            role.description = role.description or description

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Roles could not be seeded", 400)

    roles = db.session.scalars(select(Role).order_by(Role.id)).all()
    return jsonify({"status": "success", "data": [_serialize_role(role) for role in roles]})


@roles_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_role():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)

    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        return _error("name is required", 400)

    role = Role(
        name=name.strip().upper(),
        description=payload.get("description"),
    )
    db.session.add(role)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Role already exists or data is invalid", 400)

    return jsonify({"status": "success", "data": _serialize_role(role)}), 201


def _serialize_role(role):
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "created_at": role.created_at.isoformat() if role.created_at else None,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
