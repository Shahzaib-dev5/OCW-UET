from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.course import AccessLevel, Course, CourseLevel, CourseStatus
from app.models.department import Department
from app.services.authz import (
    ADMIN,
    can_manage_course,
    can_view_course_record,
    can_view_course_learning,
    current_user,
    enrollment_status_for,
    is_approved_instructor,
    is_admin,
    require_roles,
)


courses_bp = Blueprint(
    "courses",
    __name__,
    url_prefix="/api/courses"
)


@courses_bp.route("", methods=["GET"])
def get_courses():
    try:
        query = _visible_courses_query().order_by(Course.display_order, Course.id)
        courses = db.session.scalars(query).all()
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
        
        query = (
            _visible_courses_query()
            .where(Course.department_id == department_id)
            .order_by(Course.display_order, Course.id)
        )
        courses = db.session.scalars(query).all()
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
    if not can_view_course_record(course):
        return _error("Course is awaiting admin approval", 404)

    return jsonify({
        "status": "success",
        "data": _serialize_course(course)
    })


@courses_bp.route("", methods=["POST"])
def create_course():
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    if not is_admin(user) and not is_approved_instructor(user):
        return _error("Only admin or approved instructors can create courses", 403)
    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error

    if not is_admin(user):
        values["owner_id"] = user.id
        values.setdefault("instructor_name", user.full_name or user.username)
        values.setdefault("instructor_email", user.email)
        values["status"] = CourseStatus.DRAFT
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
def update_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        return _error("Course not found", 404)
    if not can_manage_course(course_id):
        return _error("Only admin or the approved course owner can update this course", 403)

    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=False)
    if error:
        return error
    if not is_admin(current_user()) and values.get("status") == CourseStatus.PUBLISHED:
        return _error("Only admin can publish or approve instructor courses", 403)

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
def delete_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        return _error("Course not found", 404)
    if not can_manage_course(course_id):
        return _error("Only admin or the approved course owner can delete this course", 403)

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
    "owner_id",
    "course_code",
    "title",
    "slug",
    "short_description",
    "description",
    "category",
    "credit_hours",
    "duration",
    "course_type",
    "syllabus",
    "learning_outcomes",
    "schedule",
    "access_level",
    "login_required",
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


def _visible_courses_query():
    query = select(Course)
    user = current_user()
    if user is None:
        return query.where(Course.status == CourseStatus.PUBLISHED)
    if is_admin(user):
        return query
    if is_approved_instructor(user):
        return query.where((Course.status == CourseStatus.PUBLISHED) | (Course.owner_id == user.id))
    return query.where(Course.status == CourseStatus.PUBLISHED)




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

    if "owner_id" in payload and payload["owner_id"] is not None:
        user = current_user()
        if not is_admin(user):
            return None, _error("Only admins can assign course ownership", 403)
        if not isinstance(payload["owner_id"], int) or payload["owner_id"] <= 0:
            return None, _error("owner_id must be a positive integer or null", 400)

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
    if "category" in values and values["category"] is not None and not isinstance(values["category"], str):
        return None, _error("category must be a string or null", 400)
    if "credit_hours" in values and values["credit_hours"] is not None:
        if not isinstance(values["credit_hours"], int) or values["credit_hours"] < 0:
            return None, _error("credit_hours must be a non-negative integer or null", 400)
    if "duration" in values and values["duration"] is not None and not isinstance(values["duration"], str):
        return None, _error("duration must be a string or null", 400)
    if "course_type" in values and values["course_type"] is not None and not isinstance(values["course_type"], str):
        return None, _error("course_type must be a string or null", 400)
    if "syllabus" in values and values["syllabus"] is not None and not isinstance(values["syllabus"], str):
        return None, _error("syllabus must be a string or null", 400)
    if "learning_outcomes" in values and values["learning_outcomes"] is not None and not isinstance(values["learning_outcomes"], str):
        return None, _error("learning_outcomes must be a string or null", 400)
    if "schedule" in values and values["schedule"] is not None and not isinstance(values["schedule"], str):
        return None, _error("schedule must be a string or null", 400)
    if "access_level" in values and values["access_level"] is not None:
        try:
            values["access_level"] = AccessLevel(str(values["access_level"]).upper())
        except (TypeError, ValueError):
            allowed = ", ".join(item.value for item in AccessLevel)
            return None, _error(f"access_level must be one of: {allowed}", 400)
    if "login_required" in values and values["login_required"] is not None:
        if not isinstance(values["login_required"], bool):
            return None, _error("login_required must be a boolean", 400)
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
    can_access = can_view_course_learning(course.id)
    return {
        "id": course.id,
        "department_id": course.department_id,
        "owner_id": course.owner_id,
        "department": _serialize_department(department) if department else None,
        "course_code": course.course_code,
        "title": course.title,
        "slug": course.slug,
        "short_description": course.short_description,
        "description": course.description,
        "category": course.category,
        "credit_hours": course.credit_hours,
        "duration": course.duration,
        "course_type": course.course_type,
        "syllabus": course.syllabus,
        "learning_outcomes": course.learning_outcomes,
        "schedule": course.schedule,
        "access_level": course.access_level.value if course.access_level else "PUBLIC",
        "login_required": course.login_required,
        "can_access_materials": can_access,
        "can_manage": can_manage_course(course.id),
        "enrollment": enrollment_status_for("COURSE", course.id),
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
