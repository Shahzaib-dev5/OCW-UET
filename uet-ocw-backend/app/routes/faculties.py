from flask import Blueprint, jsonify, request
from sqlalchemy import case, select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.faculty import Faculty
from app.services.authz import ADMIN, require_roles

faculties_bp = Blueprint(
    "faculties",
    __name__,
    url_prefix="/api/faculties"
)


@faculties_bp.route("", methods=["GET"])
def get_faculties():
    try:
        faculties = db.session.scalars(
            _ordered_faculty_query()
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check DB_USER and DB_PASSWORD in .env", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_faculty(faculty) for faculty in faculties]
    })


@faculties_bp.route("/<int:faculty_id>", methods=["GET"])
def get_faculty(faculty_id):
    try:
        faculty = db.session.get(Faculty, faculty_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check DB_USER and DB_PASSWORD in .env", 503)
    if faculty is None:
        return _error("Faculty not found", 404)

    return jsonify({
        "status": "success",
        "data": _serialize_faculty(faculty)
    })


@faculties_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_faculty():
    payload, error = _get_payload()
    if error:
        return error

    faculty, error = _build_faculty(payload)
    if error:
        return error

    db.session.add(faculty)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("A faculty with this name already exists", 409)

    return jsonify({
        "status": "success",
        "data": _serialize_faculty(faculty)
    }), 201


@faculties_bp.route("/<int:faculty_id>", methods=["PUT", "PATCH"])
@require_roles(ADMIN)
def update_faculty(faculty_id):
    faculty = db.session.get(Faculty, faculty_id)
    if faculty is None:
        return _error("Faculty not found", 404)

    payload, error = _get_payload()
    if error:
        return error

    unknown_fields = set(payload) - _FACULTY_FIELDS
    if unknown_fields:
        return _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    for field in payload:
        value = payload[field]
        if field == "name":
            if not isinstance(value, str) or not value.strip():
                return _error("name must be a non-empty string", 400)
            value = value.strip()
        if field == "display_order":
            value, error = _display_order_value({"display_order": value})
            if error:
                return error
        setattr(faculty, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("A faculty with this name already exists", 409)

    return jsonify({
        "status": "success",
        "data": _serialize_faculty(faculty)
    })


@faculties_bp.route("/<int:faculty_id>", methods=["DELETE"])
@require_roles(ADMIN)
def delete_faculty(faculty_id):
    faculty = db.session.get(Faculty, faculty_id)
    if faculty is None:
        return _error("Faculty not found", 404)

    db.session.delete(faculty)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Faculty cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Faculty deleted successfully"
    })


_FACULTY_FIELDS = {
    "name",
    "short_name",
    "description",
    "logo",
    "website_url",
    "display_order",
    "is_active",
}


def _get_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object", 400)
    return payload, None


def _build_faculty(payload):
    unknown_fields = set(payload) - _FACULTY_FIELDS
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)
    if not isinstance(payload.get("name"), str) or not payload["name"].strip():
        return None, _error("name must be a non-empty string", 400)

    values = dict(payload)
    values["name"] = values["name"].strip()
    display_order, error = _display_order_value(values)
    if error:
        return None, error
    if "display_order" in values:
        values["display_order"] = display_order
    return Faculty(**values), None


def _ordered_faculty_query():
    return select(Faculty).order_by(
        case(
            (Faculty.display_order.is_(None), 1),
            (Faculty.display_order <= 0, 1),
            else_=0,
        ),
        Faculty.display_order,
        Faculty.id,
    )


def _display_order_value(values):
    if "display_order" not in values or values["display_order"] is None:
        return None, None

    value = values["display_order"]
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    if not isinstance(value, int):
        return None, _error("display_order must be an integer or null", 400)
    return value, None


def _serialize_faculty(faculty):
    return {
        "id": faculty.id,
        "name": faculty.name,
        "short_name": faculty.short_name,
        "description": faculty.description,
        "logo": faculty.logo,
        "website_url": faculty.website_url,
        "display_order": faculty.display_order,
        "is_active": faculty.is_active,
        "created_at": faculty.created_at.isoformat() if faculty.created_at else None,
        "updated_at": faculty.updated_at.isoformat() if faculty.updated_at else None,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
