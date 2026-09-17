from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.course import Course
from app.models.enrollment import ApplicationStatus, CourseTeachingApplication
from app.models.user import User
from app.services.authz import (
    ADMIN,
    TEACHER,
    current_user,
    require_roles,
    role_name,
)
from app.services.db_setup import ensure_rbac_tables


course_teaching_applications_bp = Blueprint(
    "course_teaching_applications",
    __name__,
    url_prefix="/api/course-teaching-applications",
)


@course_teaching_applications_bp.route("", methods=["GET"])
def get_teaching_applications():
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)

    query = select(CourseTeachingApplication).order_by(CourseTeachingApplication.id.desc())
    if role_name(user) == TEACHER:
        query = query.where(CourseTeachingApplication.teacher_id == user.id)
    elif role_name(user) != ADMIN:
        return _error("You do not have permission to view teaching applications", 403)

    try:
        applications = db.session.scalars(query).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({"status": "success", "data": [_serialize_application(item) for item in applications]})


@course_teaching_applications_bp.route("", methods=["POST"])
@require_roles(TEACHER)
def apply_to_teach_course():
    user = current_user()
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)

    payload, error = _get_payload()
    if error:
        return error

    course_id = payload.get("course_id")
    if not isinstance(course_id, int) or course_id <= 0:
        return _error("course_id must be a positive integer", 400)
    if db.session.get(Course, course_id) is None:
        return _error("Course not found", 404)

    existing = db.session.scalar(
        select(CourseTeachingApplication).where(
            CourseTeachingApplication.teacher_id == user.id,
            CourseTeachingApplication.course_id == course_id,
        )
    )
    if existing is not None:
        if existing.status == ApplicationStatus.REJECTED:
            existing.status = ApplicationStatus.PENDING
            existing.reviewed_by = None
            existing.reviewed_at = None
            existing.message = payload.get("message")
            db.session.commit()
        return jsonify({"status": "success", "data": _serialize_application(existing)})

    application = CourseTeachingApplication(
        teacher_id=user.id,
        course_id=course_id,
        message=payload.get("message"),
    )
    db.session.add(application)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Teacher already applied for this course", 409)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable or the application table could not be created", 503)

    return jsonify({"status": "success", "data": _serialize_application(application)}), 201


@course_teaching_applications_bp.route("/<int:application_id>/approve", methods=["PATCH"])
@require_roles(ADMIN)
def approve_teaching_application(application_id):
    return _review_application(application_id, ApplicationStatus.APPROVED)


@course_teaching_applications_bp.route("/<int:application_id>/reject", methods=["PATCH"])
@require_roles(ADMIN)
def reject_teaching_application(application_id):
    return _review_application(application_id, ApplicationStatus.REJECTED)


@course_teaching_applications_bp.route("/teacher/<int:teacher_id>", methods=["GET"])
def get_teaching_applications_by_teacher(teacher_id):
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)
    if role_name(user) != ADMIN and user.id != teacher_id:
        return _error("You can only view your own teaching applications", 403)

    if db.session.get(User, teacher_id) is None:
        return _error("Teacher not found", 404)

    applications = db.session.scalars(
        select(CourseTeachingApplication)
        .where(CourseTeachingApplication.teacher_id == teacher_id)
        .order_by(CourseTeachingApplication.id.desc())
    ).all()
    return jsonify({"status": "success", "data": [_serialize_application(item) for item in applications]})


@course_teaching_applications_bp.route("/course/<int:course_id>", methods=["GET"])
@require_roles(ADMIN)
def get_teaching_applications_by_course(course_id):
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)

    if db.session.get(Course, course_id) is None:
        return _error("Course not found", 404)

    applications = db.session.scalars(
        select(CourseTeachingApplication)
        .where(CourseTeachingApplication.course_id == course_id)
        .order_by(CourseTeachingApplication.id.desc())
    ).all()
    return jsonify({"status": "success", "data": [_serialize_application(item) for item in applications]})


def _review_application(application_id, status):
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)

    application = db.session.get(CourseTeachingApplication, application_id)
    if application is None:
        return _error("Teaching application not found", 404)

    payload = request.get_json(silent=True) or {}
    application.status = status
    application.reviewed_by = current_user().id
    application.reviewed_at = datetime.utcnow()
    if "message" in payload:
        application.message = payload["message"]

    db.session.commit()
    return jsonify({"status": "success", "data": _serialize_application(application)})


def _get_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object", 400)
    if "course_id" in payload and isinstance(payload["course_id"], str) and payload["course_id"].isdigit():
        payload["course_id"] = int(payload["course_id"])
    unknown_fields = set(payload) - {"course_id", "message"}
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)
    if "message" in payload and payload["message"] is not None and not isinstance(payload["message"], str):
        return None, _error("message must be a string or null", 400)
    return payload, None


def _serialize_application(application):
    return {
        "id": application.id,
        "teacher_id": application.teacher_id,
        "teacher": _serialize_user(application.teacher) if application.teacher else None,
        "course_id": application.course_id,
        "course": _serialize_course(application.course) if application.course else None,
        "status": application.status.value if application.status else None,
        "message": application.message,
        "reviewed_by": application.reviewed_by,
        "reviewed_at": application.reviewed_at.isoformat() if application.reviewed_at else None,
        "created_at": application.created_at.isoformat() if application.created_at else None,
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
    }


def _serialize_course(course):
    return {"id": course.id, "title": course.title, "slug": course.slug, "department_id": course.department_id}


def _serialize_user(user):
    return {"id": user.id, "username": user.username, "email": user.email, "full_name": user.full_name}


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
