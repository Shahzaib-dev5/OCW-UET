from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.department import Department, DepartmentType
from app.models.faculty import Faculty
from app.services.authz import ADMIN, require_roles


departments_bp = Blueprint(
    "departments",
    __name__,
    url_prefix="/api/departments"
)


@departments_bp.route("", methods=["GET"])
def get_departments():
    try:
        departments = db.session.scalars(
            select(Department).order_by(Department.display_order, Department.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_department(department) for department in departments]
    })


@departments_bp.route("/faculty/<int:faculty_id>", methods=["GET"])
def get_departments_by_faculty(faculty_id):
    try:
        # Verify faculty exists
        faculty = db.session.get(Faculty, faculty_id)
        if faculty is None:
            return _error("Faculty not found", 404)
        
        departments = db.session.scalars(
            select(Department)
            .where(Department.faculty_id == faculty_id)
            .order_by(Department.display_order, Department.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_department(department) for department in departments]
    })


@departments_bp.route("/<int:department_id>", methods=["GET"])
def get_department(department_id):
    try:
        department = db.session.get(Department, department_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    if department is None:
        return _error("Department not found", 404)

    return jsonify({
        "status": "success",
        "data": _serialize_department(department)
    })


@departments_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_department():
    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_name=True)
    if error:
        return error

    department = Department(**values)
    db.session.add(department)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected faculty does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_department(department)
    }), 201


@departments_bp.route("/<int:department_id>", methods=["PUT", "PATCH"])
@require_roles(ADMIN)
def update_department(department_id):
    department = db.session.get(Department, department_id)
    if department is None:
        return _error("Department not found", 404)

    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_name=False)
    if error:
        return error

    for field, value in values.items():
        setattr(department, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected faculty does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_department(department)
    })


@departments_bp.route("/<int:department_id>", methods=["DELETE"])
@require_roles(ADMIN)
def delete_department(department_id):
    department = db.session.get(Department, department_id)
    if department is None:
        return _error("Department not found", 404)

    db.session.delete(department)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Department cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Department deleted successfully"
    })


_DEPARTMENT_FIELDS = {
    "faculty_id",
    "name",
    "short_name",
    "department_type",
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


def _validated_values(payload, require_name):
    unknown_fields = set(payload) - _DEPARTMENT_FIELDS
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    if require_name and "name" not in payload:
        return None, _error("name is required", 400)
    if "name" in payload and (
        not isinstance(payload["name"], str) or not payload["name"].strip()
    ):
        return None, _error("name must be a non-empty string", 400)

    values = dict(payload)
    if "name" in values:
        values["name"] = values["name"].strip()

    if "department_type" in values:
        try:
            values["department_type"] = DepartmentType(values["department_type"])
        except (TypeError, ValueError):
            allowed = ", ".join(item.value for item in DepartmentType)
            return None, _error(f"department_type must be one of: {allowed}", 400)

    if "faculty_id" in values and values["faculty_id"] is not None:
        if not isinstance(values["faculty_id"], int) or values["faculty_id"] <= 0:
            return None, _error("faculty_id must be a positive integer or null", 400)
        if db.session.get(Faculty, values["faculty_id"]) is None:
            return None, _error("Faculty not found", 404)

    return values, None


def _serialize_department(department):
    faculty = department.faculty
    return {
        "id": department.id,
        "faculty_id": department.faculty_id,
        "faculty": _serialize_faculty(faculty) if faculty else None,
        "name": department.name,
        "short_name": department.short_name,
        "department_type": department.department_type.value,
        "description": department.description,
        "logo": department.logo,
        "website_url": department.website_url,
        "display_order": department.display_order,
        "is_active": department.is_active,
        "created_at": department.created_at.isoformat() if department.created_at else None,
        "updated_at": department.updated_at.isoformat() if department.updated_at else None,
    }


def _serialize_faculty(faculty):
    return {
        "id": faculty.id,
        "name": faculty.name,
        "short_name": faculty.short_name,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
