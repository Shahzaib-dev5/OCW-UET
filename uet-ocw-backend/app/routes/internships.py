from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.department import Department
from app.models.internship import Internship, InternshipStatus
from app.services.authz import ADMIN, require_roles


internships_bp = Blueprint(
    "internships",
    __name__,
    url_prefix="/api/internships"
)

skills_development_bp = Blueprint(
    "skills_development",
    __name__,
    url_prefix="/api/skills-development"
)


@skills_development_bp.route("", methods=["GET"])
@internships_bp.route("", methods=["GET"])
def get_internships():
    try:
        internships = db.session.scalars(
            select(Internship).order_by(Internship.display_order, Internship.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_internship(internship) for internship in internships]
    })


@skills_development_bp.route("/department/<int:department_id>", methods=["GET"])
@internships_bp.route("/department/<int:department_id>", methods=["GET"])
def get_internships_by_department(department_id):
    try:
        # Verify department exists
        department = db.session.get(Department, department_id)
        if department is None:
            return _error("Department not found", 404)
        
        internships = db.session.scalars(
            select(Internship)
            .where(Internship.department_id == department_id)
            .order_by(Internship.display_order, Internship.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_internship(internship) for internship in internships]
    })


@skills_development_bp.route("/<int:internship_id>", methods=["GET"])
@internships_bp.route("/<int:internship_id>", methods=["GET"])
def get_internship(internship_id):
    try:
        internship = db.session.get(Internship, internship_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    if internship is None:
        return _error("Skills development program not found", 404)

    return jsonify({
        "status": "success",
        "data": _serialize_internship(internship)
    })


@skills_development_bp.route("", methods=["POST"])
@internships_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_internship():
    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error

    internship = Internship(**values)
    db.session.add(internship)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected department does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_internship(internship)
    }), 201


@skills_development_bp.route("/<int:internship_id>", methods=["PUT", "PATCH"])
@internships_bp.route("/<int:internship_id>", methods=["PUT", "PATCH"])
@require_roles(ADMIN)
def update_internship(internship_id):
    internship = db.session.get(Internship, internship_id)
    if internship is None:
        return _error("Skills development program not found", 404)

    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=False)
    if error:
        return error

    for field, value in values.items():
        setattr(internship, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected department does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_internship(internship)
    })


@skills_development_bp.route("/<int:internship_id>", methods=["DELETE"])
@internships_bp.route("/<int:internship_id>", methods=["DELETE"])
@require_roles(ADMIN)
def delete_internship(internship_id):
    internship = db.session.get(Internship, internship_id)
    if internship is None:
        return _error("Skills development program not found", 404)

    db.session.delete(internship)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Skills development program cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Skills development program deleted successfully"
    })


_INTERNSHIP_FIELDS = {
    "department_id",
    "title",
    "slug",
    "description",
    "category",
    "duration",
    "eligibility",
    "application_url",
    "thumbnail",
    "start_date",
    "end_date",
    "status",
    "display_order",
}


def _get_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object", 400)
    return payload, None


def _validated_values(payload, require_required_fields):
    unknown_fields = set(payload) - _INTERNSHIP_FIELDS
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    if require_required_fields:
        required_fields = ["department_id", "title", "slug"]
        for field in required_fields:
            if field not in payload:
                return None, _error(f"{field} is required", 400)

    if "department_id" in payload and payload["department_id"] is not None:
        if not isinstance(payload["department_id"], int) or payload["department_id"] <= 0:
            return None, _error("department_id must be a positive integer or null", 400)
        if db.session.get(Department, payload["department_id"]) is None:
            return None, _error("Department not found", 404)

    if "title" in payload:
        if not isinstance(payload["title"], str) or not payload["title"].strip():
            return None, _error("title must be a non-empty string", 400)

    if "slug" in payload:
        if not isinstance(payload["slug"], str) or not payload["slug"].strip():
            return None, _error("slug must be a non-empty string", 400)

    values = dict(payload)
    if "title" in values:
        values["title"] = values["title"].strip()
    if "slug" in values:
        values["slug"] = values["slug"].strip()

    for field_name in [
        "description",
        "category",
        "duration",
        "eligibility",
        "application_url",
        "thumbnail",
    ]:
        if field_name in values and values[field_name] is not None and not isinstance(values[field_name], str):
            return None, _error(f"{field_name} must be a string or null", 400)

    for field_name in ["start_date", "end_date"]:
        if field_name in values and values[field_name] is not None:
            try:
                values[field_name] = _parse_date(values[field_name])
            except ValueError:
                return None, _error(f"{field_name} must be a valid date in YYYY-MM-DD format", 400)

    if "status" in values and values["status"] is not None:
        try:
            values["status"] = InternshipStatus(values["status"])
        except (TypeError, ValueError):
            allowed = ", ".join(item.value for item in InternshipStatus)
            return None, _error(f"status must be one of: {allowed}", 400)

    if "display_order" in values and values["display_order"] is not None:
        if not isinstance(values["display_order"], int):
            return None, _error("display_order must be an integer or null", 400)

    return values, None


def _parse_date(value):
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError from exc
    raise ValueError


def _serialize_internship(internship):
    department = internship.department
    return {
        "id": internship.id,
        "department_id": internship.department_id,
        "department": _serialize_department(department) if department else None,
        "title": internship.title,
        "slug": internship.slug,
        "description": internship.description,
        "category": internship.category,
        "duration": internship.duration,
        "eligibility": internship.eligibility,
        "application_url": internship.application_url,
        "thumbnail": internship.thumbnail,
        "start_date": internship.start_date.isoformat() if internship.start_date else None,
        "end_date": internship.end_date.isoformat() if internship.end_date else None,
        "status": internship.status.value if internship.status is not None else None,
        "display_order": internship.display_order,
        "created_at": internship.created_at.isoformat() if internship.created_at else None,
        "updated_at": internship.updated_at.isoformat() if internship.updated_at else None,
    }


def _serialize_department(department):
    return {
        "id": department.id,
        "faculty_id": department.faculty_id,
        "name": department.name,
        "short_name": department.short_name,
        "department_type": department.department_type.value if department.department_type else None,
        "is_active": department.is_active,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
