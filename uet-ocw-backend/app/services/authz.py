from functools import wraps

from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from sqlalchemy import exists, select

from app.extensions import db
from app.models.enrollment import ApplicationStatus, CourseEnrollment, CourseTeachingApplication
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


def can_manage_course(course_id):
    user = current_user()
    if user is None:
        return False
    if role_name(user) == ADMIN:
        return True
    if role_name(user) != TEACHER:
        return False

    return db.session.scalar(
        select(
            exists().where(
                CourseTeachingApplication.teacher_id == user.id,
                CourseTeachingApplication.course_id == course_id,
                CourseTeachingApplication.status == ApplicationStatus.APPROVED,
            )
        )
    )


def can_view_course_resources(course_id):
    user = current_user()
    if user is None:
        return True
    if role_name(user) in {ADMIN, TEACHER}:
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


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
