from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.course import Course
from app.models.lecture import Lecture
from app.services.authz import can_manage_course, can_view_course_learning, can_view_course_record, can_view_course_resources, current_user


lectures_bp = Blueprint(
    "lectures",
    __name__,
    url_prefix="/api/lectures"
)


@lectures_bp.route("", methods=["GET"])
def get_lectures():
    try:
        query = select(Lecture).order_by(Lecture.display_order, Lecture.id)
        from app.services.authz import approved_student_course_ids, role_name, STUDENT

        if current_user() is not None and role_name() == STUDENT:
            query = query.where(Lecture.course_id.in_(approved_student_course_ids() or []))

        lectures = db.session.scalars(query).all()
        lectures = [lecture for lecture in lectures if lecture.course and can_view_course_record(lecture.course)]
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_lecture(lecture) for lecture in lectures]
    })


@lectures_bp.route("/course/<int:course_id>", methods=["GET"])
def get_lectures_by_course(course_id):
    try:
        course = db.session.get(Course, course_id)
        if course is None:
            return _error("Course not found", 404)
        if not can_view_course_record(course):
            return _error("Course is awaiting admin approval", 404)
        lectures = db.session.scalars(
            select(Lecture)
            .where(Lecture.course_id == course_id)
            .order_by(Lecture.display_order, Lecture.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_lecture(lecture) for lecture in lectures]
    })


@lectures_bp.route("/<int:lecture_id>", methods=["GET"])
def get_lecture(lecture_id):
    try:
        lecture = db.session.get(Lecture, lecture_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    if lecture is None:
        return _error("Lecture not found", 404)
    if lecture.course and not can_view_course_record(lecture.course):
        return _error("Lecture not found", 404)
    if not can_view_course_resources(lecture.course_id):
        return _error("You must be approved for this course before viewing lectures", 403)

    return jsonify({
        "status": "success",
        "data": _serialize_lecture(lecture)
    })


@lectures_bp.route("", methods=["POST"])
def create_lecture():
    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error
    if not can_manage_course(values["course_id"]):
        return _error("Only admin or an approved teacher can add lectures for this course", 403)

    lecture = Lecture(**values)
    db.session.add(lecture)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected course does not exist or the lecture number already exists for this course", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_lecture(lecture)
    }), 201


@lectures_bp.route("/<int:lecture_id>", methods=["PUT", "PATCH"])
def update_lecture(lecture_id):
    lecture = db.session.get(Lecture, lecture_id)
    if lecture is None:
        return _error("Lecture not found", 404)

    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=False)
    if error:
        return error
    target_course_id = values.get("course_id", lecture.course_id)
    if not can_manage_course(target_course_id):
        return _error("Only admin or an approved teacher can update lectures for this course", 403)

    for field, value in values.items():
        setattr(lecture, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected course does not exist or the lecture number already exists for this course", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_lecture(lecture)
    })


@lectures_bp.route("/<int:lecture_id>", methods=["DELETE"])
def delete_lecture(lecture_id):
    lecture = db.session.get(Lecture, lecture_id)
    if lecture is None:
        return _error("Lecture not found", 404)
    if not can_manage_course(lecture.course_id):
        return _error("Only admin or an approved teacher can delete lectures for this course", 403)

    db.session.delete(lecture)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Lecture cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Lecture deleted successfully"
    })


_LECTURE_FIELDS = {
    "course_id",
    "lecture_number",
    "title",
    "description",
    "duration_minutes",
    "video_url",
    "presentation_url",
    "notes_url",
    "is_published",
    "display_order",
}


def _get_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object", 400)
    return payload, None


def _validated_values(payload, require_required_fields):
    unknown_fields = set(payload) - _LECTURE_FIELDS
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    if require_required_fields:
        required_fields = ["course_id", "lecture_number", "title"]
        for field in required_fields:
            if field not in payload:
                return None, _error(f"{field} is required", 400)

    if "course_id" in payload and payload["course_id"] is not None:
        if not isinstance(payload["course_id"], int) or payload["course_id"] <= 0:
            return None, _error("course_id must be a positive integer or null", 400)
        if db.session.get(Course, payload["course_id"]) is None:
            return None, _error("Course not found", 404)

    if "lecture_number" in payload:
        if not isinstance(payload["lecture_number"], int) or payload["lecture_number"] <= 0:
            return None, _error("lecture_number must be a positive integer", 400)

    if "title" in payload:
        if not isinstance(payload["title"], str) or not payload["title"].strip():
            return None, _error("title must be a non-empty string", 400)

    values = dict(payload)
    if "title" in values:
        values["title"] = values["title"].strip()

    for field_name in ["description", "video_url", "presentation_url", "notes_url"]:
        if field_name in values and values[field_name] is not None and not isinstance(values[field_name], str):
            return None, _error(f"{field_name} must be a string or null", 400)

    if "duration_minutes" in values and values["duration_minutes"] is not None:
        if not isinstance(values["duration_minutes"], int) or values["duration_minutes"] < 0:
            return None, _error("duration_minutes must be a non-negative integer or null", 400)

    if "display_order" in values and values["display_order"] is not None:
        if not isinstance(values["display_order"], int):
            return None, _error("display_order must be an integer or null", 400)

    if "is_published" in values and values["is_published"] is not None:
        if not isinstance(values["is_published"], bool):
            return None, _error("is_published must be a boolean or null", 400)

    return values, None


def _serialize_lecture(lecture):
    course = lecture.course
    can_access = can_view_course_learning(lecture.course_id)
    return {
        "id": lecture.id,
        "course_id": lecture.course_id,
        "course": _serialize_course(course) if course else None,
        "lecture_number": lecture.lecture_number,
        "title": lecture.title,
        "description": lecture.description,
        "duration_minutes": lecture.duration_minutes,
        "video_url": lecture.video_url if can_access else None,
        "presentation_url": lecture.presentation_url if can_access else None,
        "notes_url": lecture.notes_url if can_access else None,
        "locked": not can_access,
        "is_published": lecture.is_published,
        "display_order": lecture.display_order,
        "created_at": lecture.created_at.isoformat() if lecture.created_at else None,
        "updated_at": lecture.updated_at.isoformat() if lecture.updated_at else None,
    }


def _serialize_course(course):
    return {
        "id": course.id,
        "department_id": course.department_id,
        "title": course.title,
        "slug": course.slug,
        "course_code": course.course_code,
        "status": course.status.value if course.status is not None else None,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
