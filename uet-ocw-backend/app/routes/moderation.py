from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.course import Course, CourseStatus
from app.models.course_review import CourseReview
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.user import User
from app.routes.courses import _serialize_course
from app.routes.course_resources import _serialize_resource
from app.routes.lectures import _serialize_lecture
from app.services.authz import ADMIN, MODERATOR, current_user, require_roles


moderation_bp = Blueprint("moderation", __name__, url_prefix="/api/moderation")


@moderation_bp.get("/filters")
@require_roles(ADMIN, MODERATOR)
def filters():
    faculties = db.session.scalars(select(Faculty).order_by(Faculty.name)).all()
    departments = db.session.scalars(select(Department).order_by(Department.name)).all()
    instructors = db.session.scalars(
        select(User).where(User.id.in_(select(Course.owner_id).where(Course.owner_id.is_not(None)))).order_by(User.full_name, User.username)
    ).all()
    return jsonify(status="success", data={
        "faculties": [{"id": row.id, "name": row.name} for row in faculties],
        "departments": [{"id": row.id, "name": row.name, "faculty_id": row.faculty_id} for row in departments],
        "instructors": [_person(row) for row in instructors],
    })


@moderation_bp.get("/courses")
@require_roles(ADMIN, MODERATOR)
def list_courses():
    query = select(Course).join(Department, Course.department_id == Department.id)
    for name, column in (("faculty_id", Department.faculty_id), ("department_id", Course.department_id), ("instructor_id", Course.owner_id)):
        value = request.args.get(name)
        if value not in (None, ""):
            number = _positive_integer(value)
            if number is None:
                return _error(f"{name} must be a positive integer", 400)
            query = query.where(column == number)
    status = request.args.get("status", "PENDING").strip().upper()
    if status not in {"PENDING", "APPROVED", "REJECTED", "ALL"}:
        return _error("status must be PENDING, APPROVED, REJECTED, or ALL", 400)
    if status != "ALL":
        query = query.where(Course.review_status == status)
        if status == "PENDING":
            query = query.where(Course.status == CourseStatus.DRAFT)
    search = request.args.get("q", "").strip()
    if len(search) > 200:
        return _error("q must be at most 200 characters", 400)
    if search:
        query = query.where(or_(Course.title.contains(search, autoescape=True), Course.course_code.contains(search, autoescape=True)))
    page = _positive_integer(request.args.get("page", "1"))
    per_page = _positive_integer(request.args.get("per_page", "20"))
    if page is None or per_page is None or per_page > 100:
        return _error("page must be positive and per_page must be between 1 and 100", 400)
    total = db.session.scalar(select(func.count()).select_from(query.subquery()))
    courses = db.session.scalars(
        query.options(joinedload(Course.owner), joinedload(Course.department).joinedload(Department.faculty), joinedload(Course.reviewer))
        .order_by(Course.updated_at.desc(), Course.id.desc()).offset((page - 1) * per_page).limit(per_page)
    ).all()
    return jsonify(status="success", data=[_course(row) for row in courses], pagination={
        "page": page, "per_page": per_page, "total": total, "pages": (total + per_page - 1) // per_page,
    })


@moderation_bp.get("/courses/<int:course_id>")
@require_roles(ADMIN, MODERATOR)
def course_detail(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        return _error("Course not found", 404)
    return jsonify(status="success", data=_course(course, include_content=True))


@moderation_bp.post("/courses/<int:course_id>/approve")
@require_roles(ADMIN, MODERATOR)
def approve_course(course_id):
    return _review(course_id, "APPROVED")


@moderation_bp.post("/courses/<int:course_id>/reject")
@require_roles(ADMIN, MODERATOR)
def reject_course(course_id):
    return _review(course_id, "REJECTED")


def _review(course_id, status):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)
    unknown = set(payload) - {"reason", "review_version"}
    if unknown:
        return _error(f"Unknown fields: {', '.join(sorted(unknown))}", 400)
    version = payload.get("review_version")
    if type(version) is not int or version < 0:
        return _error("review_version must be the non-negative integer returned by the course preview", 400)
    reason = payload.get("reason")
    if reason is not None and not isinstance(reason, str):
        return _error("reason must be a string", 400)
    reason = reason.strip() if reason else None
    if status == "REJECTED" and not reason:
        return _error("A rejection reason is required", 400)
    if reason and len(reason) > 2000:
        return _error("reason must be at most 2000 characters", 400)
    if db.session.get(Course, course_id) is None:
        return _error("Course not found", 404)
    user = current_user()
    reviewed_at = datetime.utcnow()
    # A single conditional UPDATE serializes decisions with edits and other reviews.
    result = db.session.execute(update(Course).where(Course.id == course_id, Course.review_version == version).values(
        status=CourseStatus.PUBLISHED if status == "APPROVED" else CourseStatus.DRAFT,
        review_status=status, review_reason=reason, reviewed_by=user.id,
        reviewed_at=reviewed_at, review_version=version + 1,
    ))
    if result.rowcount != 1:
        db.session.rollback()
        return _error("This course changed after your preview. Reload it before reviewing", 409)
    db.session.add(CourseReview(course_id=course_id, status=status, reason=reason, reviewed_by=user.id,
                               reviewed_at=reviewed_at, review_version=version + 1))
    db.session.commit()
    return jsonify(status="success", message=f"Course {status.lower()} successfully", data=_course(db.session.get(Course, course_id), include_content=True))


def _course(course, include_content=False):
    data = _serialize_course(course)
    faculty = course.department.faculty if course.department else None
    data.update(
        faculty={"id": faculty.id, "name": faculty.name} if faculty else None,
        submitted_by=_person(course.owner), review_status=course.review_status,
        review_reason=course.review_reason, reviewed_by=_person(course.reviewer),
        reviewed_at=course.reviewed_at.isoformat() if course.reviewed_at else None,
        review_version=course.review_version,
    )
    if include_content:
        data["lectures"] = [_serialize_lecture(row) for row in course.lectures]
        data["resources"] = [_serialize_resource(row) for row in course.resources]
        reviews = db.session.scalars(select(CourseReview).where(CourseReview.course_id == course.id)
                                     .options(joinedload(CourseReview.reviewer)).order_by(CourseReview.id.desc())).all()
        data["review_history"] = [{"id": row.id, "status": row.status, "reason": row.reason,
                                  "review_version": row.review_version, "reviewed_by": _person(row.reviewer),
                                  "reviewed_at": row.reviewed_at.isoformat()} for row in reviews]
    return data


def _person(user):
    if user is None:
        return None
    return {"id": user.id, "full_name": user.full_name, "username": user.username, "email": user.email}


def _positive_integer(value):
    try:
        result = int(value)
        return result if result > 0 else None
    except (TypeError, ValueError):
        return None


def _error(message, status_code):
    return jsonify(status="error", message=message), status_code
