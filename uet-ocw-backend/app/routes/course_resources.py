from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.course import AccessLevel, Course
from app.models.resource import CourseResource, CourseResourceType
from app.services.authz import can_manage_course, can_view_book_learning, can_view_course_learning, can_view_course_record, can_view_course_resources, current_user, enrollment_status_for, is_admin, is_approved_instructor


course_resources_bp = Blueprint(
    "course_resources",
    __name__,
    url_prefix="/api/course-resources"
)


@course_resources_bp.route("", methods=["GET"])
def get_course_resources():
    try:
        query = select(CourseResource).order_by(CourseResource.display_order, CourseResource.id)
        resources = db.session.scalars(query).all()
        resources = [
            resource for resource in resources
            if (resource.course and can_view_course_record(resource.course))
            or (resource.course_id is None and resource.resource_type == CourseResourceType.BOOK)
        ]
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_resource(resource) for resource in resources]
    })


@course_resources_bp.route("/course/<int:course_id>", methods=["GET"])
def get_resources_by_course(course_id):
    try:
        course = db.session.get(Course, course_id)
        if course is None:
            return _error("Course not found", 404)
        if not can_view_course_record(course):
            return _error("Course is awaiting admin approval", 404)
        resources = db.session.scalars(
            select(CourseResource)
            .where(CourseResource.course_id == course_id)
            .order_by(CourseResource.display_order, CourseResource.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_resource(resource) for resource in resources]
    })


@course_resources_bp.route("/<int:resource_id>", methods=["GET"])
def get_course_resource(resource_id):
    try:
        resource = db.session.get(CourseResource, resource_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    if resource is None:
        return _error("Course resource not found", 404)
    if resource.course and not can_view_course_record(resource.course):
        return _error("Course resource not found", 404)
    if resource.course_id is None and resource.resource_type != CourseResourceType.BOOK:
        return _error("Course resource not found", 404)
    if resource.resource_type != CourseResourceType.BOOK and not can_view_course_resources(resource.course_id):
        return _error("You must be approved for this course before viewing resources", 403)

    return jsonify({
        "status": "success",
        "data": _serialize_resource(resource)
    })


@course_resources_bp.route("", methods=["POST"])
def create_course_resource():
    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error
    if not _can_manage_resource(values):
        return _error("Only admin or an approved teacher can add resources for this course", 403)
    if values.get("resource_type") == CourseResourceType.BOOK:
        user = current_user()
        values["owner_id"] = user.id if user else None

    resource = CourseResource(**values)
    db.session.add(resource)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected course does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_resource(resource)
    }), 201


@course_resources_bp.route("/<int:resource_id>", methods=["PUT", "PATCH"])
def update_course_resource(resource_id):
    resource = db.session.get(CourseResource, resource_id)
    if resource is None:
        return _error("Course resource not found", 404)

    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=False)
    if error:
        return error
    if not _can_update_or_delete_resource(resource):
        return _error("Only admin or an approved teacher can update resources for this course", 403)

    for field, value in values.items():
        setattr(resource, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected course does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_resource(resource)
    })


@course_resources_bp.route("/<int:resource_id>", methods=["DELETE"])
def delete_course_resource(resource_id):
    resource = db.session.get(CourseResource, resource_id)
    if resource is None:
        return _error("Course resource not found", 404)
    if not _can_update_or_delete_resource(resource):
        return _error("Only admin or an approved teacher can delete resources for this course", 403)

    db.session.delete(resource)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Course resource cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Course resource deleted successfully"
    })


_COURSE_RESOURCE_FIELDS = {
    "course_id",
    "access_level",
    "title",
    "resource_type",
    "description",
    "file_url",
    "external_url",
    "thumbnail",
    "file_size",
    "mime_type",
    "lecture_number",
    "display_order",
    "is_active",
}


def _get_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object", 400)
    return payload, None


def _validated_values(payload, require_required_fields):
    unknown_fields = set(payload) - _COURSE_RESOURCE_FIELDS
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    if require_required_fields:
        required_fields = ["title", "resource_type"]
        for field in required_fields:
            if field not in payload:
                return None, _error(f"{field} is required", 400)

    if "course_id" in payload and payload["course_id"] is not None:
        if not isinstance(payload["course_id"], int) or payload["course_id"] <= 0:
            return None, _error("course_id must be a positive integer or null", 400)
        if db.session.get(Course, payload["course_id"]) is None:
            return None, _error("Course not found", 404)

    if "title" in payload:
        if not isinstance(payload["title"], str) or not payload["title"].strip():
            return None, _error("title must be a non-empty string", 400)

    values = dict(payload)
    if "title" in values:
        values["title"] = values["title"].strip()

    for field_name in ["description", "file_url", "external_url", "thumbnail", "mime_type"]:
        if field_name in values and values[field_name] is not None and not isinstance(values[field_name], str):
            return None, _error(f"{field_name} must be a string or null", 400)

    if "resource_type" in values and values["resource_type"] is not None:
        try:
            values["resource_type"] = CourseResourceType(values["resource_type"])
        except (TypeError, ValueError):
            allowed = ", ".join(item.value for item in CourseResourceType)
            return None, _error(f"resource_type must be one of: {allowed}", 400)
    if "access_level" in values and values["access_level"] is not None:
        try:
            values["access_level"] = AccessLevel(str(values["access_level"]).upper())
        except (TypeError, ValueError):
            allowed = ", ".join(item.value for item in AccessLevel)
            return None, _error(f"access_level must be one of: {allowed}", 400)

    if "file_size" in values and values["file_size"] is not None:
        if not isinstance(values["file_size"], int) or values["file_size"] < 0:
            return None, _error("file_size must be a non-negative integer or null", 400)

    if "lecture_number" in values and values["lecture_number"] is not None:
        if not isinstance(values["lecture_number"], int):
            return None, _error("lecture_number must be an integer or null", 400)

    if "display_order" in values and values["display_order"] is not None:
        if not isinstance(values["display_order"], int):
            return None, _error("display_order must be an integer or null", 400)

    if "is_active" in values and values["is_active"] is not None:
        if not isinstance(values["is_active"], bool):
            return None, _error("is_active must be a boolean or null", 400)

    return values, None


def _can_manage_resource(values):
    course_id = values.get("course_id")
    resource_type = values.get("resource_type")
    if course_id is not None:
        return can_manage_course(course_id)
    if resource_type == CourseResourceType.BOOK:
        user = current_user()
        return user is not None and (is_admin(user) or is_approved_instructor(user))
    return False


def _can_update_or_delete_resource(resource):
    user = current_user()
    if user is None:
        return False
    if is_admin(user):
        return True
    if resource.resource_type == CourseResourceType.BOOK:
        return resource.owner_id is not None and resource.owner_id == user.id
    return resource.course_id is not None and can_manage_course(resource.course_id)


def _serialize_resource(resource):
    is_book = resource.resource_type == CourseResourceType.BOOK
    can_access = can_view_book_learning(resource.id) if is_book else can_view_course_learning(resource.course_id)
    return {
        "id": resource.id,
        "course_id": resource.course_id,
        "owner_id": resource.owner_id,
        "course": _serialize_course(resource.course) if resource.course else None,
        "title": resource.title,
        "resource_type": resource.resource_type.value if resource.resource_type else None,
        "access_level": resource.access_level.value if resource.access_level else "PUBLIC",
        "can_access_materials": can_access,
        "can_manage": _can_update_or_delete_resource(resource),
        "enrollment": enrollment_status_for("BOOK", resource.id) if is_book else enrollment_status_for("COURSE", resource.course_id),
        "description": resource.description,
        "file_url": resource.file_url if can_access else None,
        "external_url": resource.external_url if can_access else None,
        "thumbnail": resource.thumbnail,
        "locked": not can_access,
        "file_size": resource.file_size,
        "mime_type": resource.mime_type,
        "lecture_number": resource.lecture_number,
        "display_order": resource.display_order,
        "is_active": resource.is_active,
        "created_at": resource.created_at.isoformat() if resource.created_at else None,
        "updated_at": resource.updated_at.isoformat() if resource.updated_at else None,
    }


def _serialize_course(course):
    return {
        "id": course.id,
        "department_id": course.department_id,
        "title": course.title,
        "slug": course.slug,
        "status": course.status.value if course.status else None,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
