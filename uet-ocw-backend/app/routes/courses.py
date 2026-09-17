from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.course import Course, CourseLevel, CourseStatus
from app.models.department import Department
from app.services.authz import ADMIN, require_roles


courses_bp = Blueprint(
    "courses",
    __name__,
    url_prefix="/api/courses"
)


@courses_bp.route("", methods=["GET"])
def get_courses():
    try:
        courses = db.session.scalars(
            select(Course).order_by(Course.display_order, Course.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_course(course) for course in courses]
    })


@courses_bp.route("/department/<int:department_id>", methods=["GET"])
def get_courses_by_department(department_id):
    try:
        # Verify department exists
        department = db.session.get(Department, department_id)
        if department is None:
            return _error("Department not found", 404)
        
        courses = db.session.scalars(
            select(Course)
            .where(Course.department_id == department_id)
            .order_by(Course.display_order, Course.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_course(course) for course in courses]
    })


@courses_bp.route("/<int:course_id>", methods=["GET"])
def get_course(course_id):
    try:
        course = db.session.get(Course, course_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    if course is None:
        return _error("Course not found", 404)

    return jsonify({
        "status": "success",
        "data": _serialize_course(course)
    })


@courses_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_course():
    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error

    course = Course(**values)
    db.session.add(course)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected department does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_course(course)
    }), 201


@courses_bp.route("/<int:course_id>", methods=["PUT", "PATCH"])
@require_roles(ADMIN)
def update_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        return _error("Course not found", 404)

    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=False)
    if error:
        return error

    for field, value in values.items():
        setattr(course, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected department does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_course(course)
    })


@courses_bp.route("/<int:course_id>", methods=["DELETE"])
@require_roles(ADMIN)
def delete_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        return _error("Course not found", 404)

    db.session.delete(course)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Course cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Course deleted successfully"
    })


_COURSE_FIELDS = {
    "department_id",
    "course_code",
    "title",
    "slug",
    "short_description",
    "description",
    "instructor_name",
    "instructor_email",
    "level",
    "semester",
    "academic_year",
    "thumbnail",
    "status",
    "display_order",
}

# This API is intentionally limited to the actual columns in the courses table.
# Department fields like name, short_name, faculty_id, logo, website_url, etc.
# are not valid for courses and must not be accepted here.


def _get_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object", 400)
    return payload, None


def _validated_values(payload, require_required_fields):
    unknown_fields = set(payload) - _COURSE_FIELDS
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
        payload["slug"] = payload["slug"].strip()

    if "course_code" in payload and payload["course_code"] is not None:
        if not isinstance(payload["course_code"], str):
            return None, _error("course_code must be a string or null", 400)

    values = dict(payload)
    if "title" in values:
        values["title"] = values["title"].strip()
    if "slug" in values:
        values["slug"] = values["slug"].strip()
    if "short_description" in values and values["short_description"] is not None and not isinstance(values["short_description"], str):
        return None, _error("short_description must be a string or null", 400)
    if "description" in values and values["description"] is not None and not isinstance(values["description"], str):
        return None, _error("description must be a string or null", 400)
    if "instructor_name" in values and values["instructor_name"] is not None and not isinstance(values["instructor_name"], str):
        return None, _error("instructor_name must be a string or null", 400)
    if "instructor_email" in values and values["instructor_email"] is not None and not isinstance(values["instructor_email"], str):
        return None, _error("instructor_email must be a string or null", 400)
    if "semester" in values and values["semester"] is not None and not isinstance(values["semester"], str):
        return None, _error("semester must be a string or null", 400)
    if "academic_year" in values and values["academic_year"] is not None and not isinstance(values["academic_year"], str):
        return None, _error("academic_year must be a string or null", 400)
    if "thumbnail" in values and values["thumbnail"] is not None and not isinstance(values["thumbnail"], str):
        return None, _error("thumbnail must be a string or null", 400)
    if "level" in values and values["level"] is not None:
        try:
            values["level"] = CourseLevel(values["level"])
        except (TypeError, ValueError):
            allowed = ", ".join(item.value for item in CourseLevel)
            return None, _error(f"level must be one of: {allowed}", 400)
    if "status" in values and values["status"] is not None:
        try:
            values["status"] = CourseStatus(values["status"])
        except (TypeError, ValueError):
            allowed = ", ".join(item.value for item in CourseStatus)
            return None, _error(f"status must be one of: {allowed}", 400)
    if "display_order" in values and values["display_order"] is not None:
        if not isinstance(values["display_order"], int):
            return None, _error("display_order must be an integer or null", 400)

    return values, None


def _serialize_course(course):
    department = course.department
    return {
        "id": course.id,
        "department_id": course.department_id,
        "department": _serialize_department(department) if department else None,
        "course_code": course.course_code,
        "title": course.title,
        "slug": course.slug,
        "short_description": course.short_description,
        "description": course.description,
        "instructor_name": course.instructor_name,
        "instructor_email": course.instructor_email,
        "level": course.level.value if course.level is not None else None,
        "semester": course.semester,
        "academic_year": course.academic_year,
        "thumbnail": course.thumbnail,
        "status": course.status.value if course.status is not None else None,
        "display_order": course.display_order,
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "updated_at": course.updated_at.isoformat() if course.updated_at else None,
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
