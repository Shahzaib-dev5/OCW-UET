from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.course import Course
from app.models.enrollment import ApplicationStatus, CourseEnrollment, CourseTeachingApplication
from app.models.resource import CourseResource
from app.models.lecture import Lecture
from app.models.user import User
from app.services.authz import (
    ADMIN,
    STUDENT,
    TEACHER,
    approved_student_course_ids,
    can_manage_course,
    current_user,
    require_roles,
    role_name,
)
from app.services.db_setup import ensure_rbac_tables


course_enrollments_bp = Blueprint(
    "course_enrollments",
    __name__,
    url_prefix="/api/course-enrollments",
)


@course_enrollments_bp.route("", methods=["GET"])
def get_course_enrollments():
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)

    query = select(CourseEnrollment).order_by(CourseEnrollment.id.desc())
    if role_name(user) == STUDENT:
        query = query.where(CourseEnrollment.student_id == user.id)
    elif role_name(user) == TEACHER:
        query = query.where(CourseEnrollment.course_id.in_(_teacher_course_ids(user.id)))
    elif role_name(user) != ADMIN:
        return _error("You do not have permission to view course enrollments", 403)

    try:
        enrollments = db.session.scalars(query).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({"status": "success", "data": [_serialize_enrollment(item) for item in enrollments]})


@course_enrollments_bp.route("", methods=["POST"])
@require_roles(STUDENT)
def apply_for_course():
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
        select(CourseEnrollment).where(
            CourseEnrollment.student_id == user.id,
            CourseEnrollment.course_id == course_id,
        )
    )
    if existing is not None:
        if existing.status == ApplicationStatus.REJECTED:
            existing.status = ApplicationStatus.PENDING
            existing.reviewed_by = None
            existing.reviewed_at = None
            existing.message = payload.get("message")
            db.session.commit()
        return jsonify({"status": "success", "data": _serialize_enrollment(existing)})

    enrollment = CourseEnrollment(
        student_id=user.id,
        course_id=course_id,
        message=payload.get("message"),
    )
    db.session.add(enrollment)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Student already applied for this course", 409)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable or the enrollment table could not be created", 503)

    return jsonify({"status": "success", "data": _serialize_enrollment(enrollment)}), 201


@course_enrollments_bp.route("/<int:enrollment_id>/approve", methods=["PATCH"])
def approve_course_enrollment(enrollment_id):
    return _review_enrollment(enrollment_id, ApplicationStatus.APPROVED)


@course_enrollments_bp.route("/<int:enrollment_id>/reject", methods=["PATCH"])
def reject_course_enrollment(enrollment_id):
    return _review_enrollment(enrollment_id, ApplicationStatus.REJECTED)


@course_enrollments_bp.route("/student/<int:student_id>", methods=["GET"])
def get_course_enrollments_by_student(student_id):
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)
    if role_name(user) != ADMIN and user.id != student_id:
        return _error("You can only view your own course enrollments", 403)

    if db.session.get(User, student_id) is None:
        return _error("Student not found", 404)

    enrollments = db.session.scalars(
        select(CourseEnrollment)
        .where(CourseEnrollment.student_id == student_id)
        .order_by(CourseEnrollment.id.desc())
    ).all()
    return jsonify({"status": "success", "data": [_serialize_enrollment(item) for item in enrollments]})


@course_enrollments_bp.route("/course/<int:course_id>", methods=["GET"])
def get_course_enrollments_by_course(course_id):
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)
    if role_name(user) != ADMIN and not can_manage_course(course_id):
        return _error("You do not have permission to view enrollments for this course", 403)
    if db.session.get(Course, course_id) is None:
        return _error("Course not found", 404)

    enrollments = db.session.scalars(
        select(CourseEnrollment)
        .where(CourseEnrollment.course_id == course_id)
        .order_by(CourseEnrollment.id.desc())
    ).all()
    return jsonify({"status": "success", "data": [_serialize_enrollment(item) for item in enrollments]})


@course_enrollments_bp.route("/me/courses", methods=["GET"])
def get_my_approved_courses():
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)

    if role_name(user) == ADMIN:
        courses = db.session.scalars(select(Course).order_by(Course.display_order, Course.id)).all()
    elif role_name(user) == TEACHER:
        courses = db.session.scalars(
            select(Course)
            .join(CourseTeachingApplication)
            .where(
                CourseTeachingApplication.teacher_id == user.id,
                CourseTeachingApplication.status == ApplicationStatus.APPROVED,
            )
            .order_by(Course.display_order, Course.id)
        ).all()
    else:
        course_ids = approved_student_course_ids() or []
        courses = db.session.scalars(
            select(Course).where(Course.id.in_(course_ids)).order_by(Course.display_order, Course.id)
        ).all()

    return jsonify({"status": "success", "data": [_serialize_course(course) for course in courses]})


@course_enrollments_bp.route("/me/resources", methods=["GET"])
def get_my_course_resources():
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)

    course_ids = _visible_course_ids(user)
    resources = db.session.scalars(
        select(CourseResource)
        .where(CourseResource.course_id.in_(course_ids))
        .order_by(CourseResource.display_order, CourseResource.id)
    ).all()
    return jsonify({"status": "success", "data": [_serialize_resource(resource) for resource in resources]})


@course_enrollments_bp.route("/me/lectures", methods=["GET"])
def get_my_course_lectures():
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)

    course_ids = _visible_course_ids(user)
    lectures = db.session.scalars(
        select(Lecture)
        .where(Lecture.course_id.in_(course_ids))
        .order_by(Lecture.display_order, Lecture.id)
    ).all()
    return jsonify({"status": "success", "data": [_serialize_lecture(lecture) for lecture in lectures]})


def _review_enrollment(enrollment_id, status):
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    try:
        ensure_rbac_tables()
    except OperationalError:
        return _error("Database is unavailable. Check your database settings", 503)

    enrollment = db.session.get(CourseEnrollment, enrollment_id)
    if enrollment is None:
        return _error("Course enrollment not found", 404)
    if role_name(user) != ADMIN and not can_manage_course(enrollment.course_id):
        return _error("Only admin or an approved teacher for this course can review enrollments", 403)

    payload = request.get_json(silent=True) or {}
    enrollment.status = status
    enrollment.reviewed_by = user.id
    enrollment.reviewed_at = datetime.utcnow()
    if "message" in payload:
        enrollment.message = payload["message"]

    db.session.commit()
    return jsonify({"status": "success", "data": _serialize_enrollment(enrollment)})


def _teacher_course_ids(teacher_id):
    return db.session.scalars(
        select(CourseTeachingApplication.course_id).where(
            CourseTeachingApplication.teacher_id == teacher_id,
            CourseTeachingApplication.status == ApplicationStatus.APPROVED,
        )
    ).all()


def _visible_course_ids(user):
    if role_name(user) == ADMIN:
        return db.session.scalars(select(Course.id)).all()
    if role_name(user) == TEACHER:
        return _teacher_course_ids(user.id)
    return approved_student_course_ids() or []


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


def _serialize_enrollment(enrollment):
    return {
        "id": enrollment.id,
        "student_id": enrollment.student_id,
        "student": _serialize_user(enrollment.student) if enrollment.student else None,
        "course_id": enrollment.course_id,
        "course": _serialize_course(enrollment.course) if enrollment.course else None,
        "status": enrollment.status.value if enrollment.status else None,
        "message": enrollment.message,
        "reviewed_by": enrollment.reviewed_by,
        "reviewed_at": enrollment.reviewed_at.isoformat() if enrollment.reviewed_at else None,
        "created_at": enrollment.created_at.isoformat() if enrollment.created_at else None,
        "updated_at": enrollment.updated_at.isoformat() if enrollment.updated_at else None,
    }


def _serialize_course(course):
    return {"id": course.id, "title": course.title, "slug": course.slug, "department_id": course.department_id}


def _serialize_resource(resource):
    return {
        "id": resource.id,
        "course_id": resource.course_id,
        "title": resource.title,
        "resource_type": resource.resource_type.value if resource.resource_type else None,
        "description": resource.description,
        "file_url": resource.file_url,
        "external_url": resource.external_url,
        "is_active": resource.is_active,
    }


def _serialize_lecture(lecture):
    return {
        "id": lecture.id,
        "course_id": lecture.course_id,
        "lecture_number": lecture.lecture_number,
        "title": lecture.title,
        "description": lecture.description,
        "video_url": lecture.video_url,
        "presentation_url": lecture.presentation_url,
        "notes_url": lecture.notes_url,
        "is_published": lecture.is_published,
    }


def _serialize_user(user):
    return {"id": user.id, "username": user.username, "email": user.email, "full_name": user.full_name}


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
