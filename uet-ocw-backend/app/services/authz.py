from functools import wraps

from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from sqlalchemy import exists, select

from app.extensions import db
from app.models.course import AccessLevel, Course, CourseStatus
from app.models.enrollment import ApplicationStatus, CourseEnrollment, CourseTeachingApplication, ResourceEnrollment, ResourceType
from app.models.internship import Internship
from app.models.resource import CourseResource
from app.models.user import User


ADMIN = "ADMIN"
TEACHER = "TEACHER"
STUDENT = "STUDENT"


def current_user():
    if hasattr(g, "current_user"):
        return g.current_user

    try:
        verify_jwt_in_request(optional=True)
        jwt_user_id = get_jwt_identity()
    except Exception:
        jwt_user_id = None

    if jwt_user_id:
        try:
            g.current_user = db.session.get(User, int(jwt_user_id))
        except (TypeError, ValueError):
            g.current_user = None
        return g.current_user

    g.current_user = None
    return None


def role_name(user=None):
    user = user or current_user()
    if user is None or user.role is None:
        return None

    name = (user.role.name or "").strip().upper()
    if name in {"STUDENTS", "STUDENT"}:
        return STUDENT
    if name in {"TEACHERS", "TEACHER", "LECTURER", "INSTRUCTOR"}:
        return TEACHER
    if name in {"ADMINS", "ADMIN", "SUPERADMIN", "SUPER_ADMIN"}:
        return ADMIN
    return name


def has_role(*roles):
    return role_name() in set(roles)


def require_roles(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                return _error("Authentication required. Send Authorization: Bearer <token>", 401)
            if role_name(user) not in set(roles):
                return _error("You do not have permission to perform this action", 403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def is_admin(user=None):
    return role_name(user) == ADMIN


def is_approved_instructor(user=None):
    user = user or current_user()
    if user is None:
        return False
    status = (user.instructor_status or "").upper()
    if status == ApplicationStatus.REVOKED.value:
        return False
    return status == ApplicationStatus.APPROVED.value or (role_name(user) == TEACHER and status in {"", "NONE"})


def can_manage_course(course_id):
    user = current_user()
    if user is None:
        return False
    if is_admin(user):
        return True
    if not is_approved_instructor(user):
        return False

    course = db.session.get(Course, course_id)
    if course is not None and course.owner_id == user.id:
        return True

    return db.session.scalar(
        select(
            exists().where(
                CourseTeachingApplication.teacher_id == user.id,
                CourseTeachingApplication.course_id == course_id,
                CourseTeachingApplication.status == ApplicationStatus.APPROVED,
            )
        )
    )


def can_view_course_record(course_or_id):
    course = course_or_id if isinstance(course_or_id, Course) else db.session.get(Course, course_or_id)
    if course is None:
        return False
    if course.status == CourseStatus.PUBLISHED:
        return True
    user = current_user()
    if user is None:
        return False
    if is_admin(user):
        return True
    return is_approved_instructor(user) and course.owner_id == user.id


def can_view_course_resources(course_id):
    return can_view_course_learning(course_id)


def can_view_course_learning(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        return False
    user = current_user()
    if course.status != CourseStatus.PUBLISHED:
        if user is None:
            return False
        if is_admin(user):
            return True
        return is_approved_instructor(user) and course.owner_id == user.id
    if course.login_required and user is None:
        return False
    if _access_value(course.access_level) == AccessLevel.PUBLIC.value:
        return True
    if user is None:
        return False
    if is_admin(user):
        return True
    if is_approved_instructor(user) and course.owner_id == user.id:
        return True

    return db.session.scalar(
        select(
            exists().where(
                CourseEnrollment.student_id == user.id,
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.status == ApplicationStatus.APPROVED,
            )
        )
    )


def course_enrollment_for_user(course_id, user=None):
    user = user or current_user()
    if user is None:
        return None
    return db.session.scalar(
        select(CourseEnrollment)
        .where(CourseEnrollment.student_id == user.id, CourseEnrollment.course_id == course_id)
        .order_by(CourseEnrollment.id.desc())
    )


def resource_enrollment_for_user(resource_type, resource_id, user=None):
    user = user or current_user()
    if user is None:
        return None
    resource_type = _resource_type(resource_type)
    if resource_type is None:
        return None
    return db.session.scalar(
        select(ResourceEnrollment)
        .where(
            ResourceEnrollment.student_id == user.id,
            ResourceEnrollment.resource_type == resource_type,
            ResourceEnrollment.resource_id == resource_id,
        )
        .order_by(ResourceEnrollment.id.desc())
    )


def can_view_book_learning(book_id):
    book = db.session.get(CourseResource, book_id)
    if book is None:
        return False
    if _access_value(book.access_level) == AccessLevel.PUBLIC.value:
        return True
    user = current_user()
    if user is None:
        return False
    if is_admin(user):
        return True
    if book.course_id and can_manage_course(book.course_id):
        return True
    if book.course_id is None and is_approved_instructor(user):
        return True
    enrollment = resource_enrollment_for_user(ResourceType.BOOK, book_id, user)
    return enrollment is not None and enrollment.status == ApplicationStatus.APPROVED


def can_view_skill_learning(skill_id):
    skill = db.session.get(Internship, skill_id)
    if skill is None:
        return False
    if _access_value(skill.access_level) == AccessLevel.PUBLIC.value:
        return True
    user = current_user()
    if user is None:
        return False
    if is_admin(user):
        return True
    enrollment = resource_enrollment_for_user(ResourceType.SKILL, skill_id, user)
    return enrollment is not None and enrollment.status == ApplicationStatus.APPROVED


def enrollment_status_for(resource_type, resource_id, user=None):
    user = user or current_user()
    if user is None:
        return None
    if _resource_type(resource_type) == ResourceType.COURSE:
        enrollment = course_enrollment_for_user(resource_id, user)
    else:
        enrollment = resource_enrollment_for_user(resource_type, resource_id, user)
    if enrollment is None:
        return None
    return {
        "id": enrollment.id,
        "status": enrollment.status.value if enrollment.status else None,
        "message": getattr(enrollment, "message", None),
        "review_reason": getattr(enrollment, "review_reason", None),
        "reviewed_at": enrollment.reviewed_at.isoformat() if enrollment.reviewed_at else None,
        "created_at": enrollment.created_at.isoformat() if enrollment.created_at else None,
    }


def approved_student_course_ids():
    user = current_user()
    if user is None or role_name(user) != STUDENT:
        return None

    return db.session.scalars(
        select(CourseEnrollment.course_id).where(
            CourseEnrollment.student_id == user.id,
            CourseEnrollment.status == ApplicationStatus.APPROVED,
        )
    ).all()


def _resource_type(value):
    if isinstance(value, ResourceType):
        return value
    try:
        return ResourceType(str(value).upper())
    except (TypeError, ValueError):
        return None


def _access_value(value):
    return value.value if hasattr(value, "value") else str(value or AccessLevel.PUBLIC.value).upper()


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
