from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from app.extensions import db
from app.models.enrollment import ApplicationStatus, InstructorApplication
from app.models.role import Role
from app.services.authz import ADMIN, current_user, require_roles, role_name

instructor_applications_bp = Blueprint(
    "instructor_applications",
    __name__,
    url_prefix="/api/instructor-applications",
)


@instructor_applications_bp.route("", methods=["GET"])
def list_applications():
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    query = select(InstructorApplication).order_by(InstructorApplication.id.desc())
    if role_name(user) != ADMIN:
        query = query.where(InstructorApplication.user_id == user.id)
    applications = db.session.scalars(query).all()
    return jsonify({"status": "success", "data": [_serialize_application(item) for item in applications]})


@instructor_applications_bp.route("/me", methods=["GET"])
def my_application():
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    application = db.session.scalar(
        select(InstructorApplication)
        .where(InstructorApplication.user_id == user.id)
        .order_by(InstructorApplication.id.desc())
    )
    return jsonify({"status": "success", "data": _serialize_application(application) if application else None})


@instructor_applications_bp.route("", methods=["POST"])
def apply():
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)
    fields = {"qualifications", "expertise", "teaching_bio", "contact_details", "affiliation"}
    unknown = set(payload) - fields
    if unknown:
        return _error(f"Unknown fields: {', '.join(sorted(unknown))}", 400)

    existing = db.session.scalar(
        select(InstructorApplication)
        .where(InstructorApplication.user_id == user.id)
        .order_by(InstructorApplication.id.desc())
    )
    if existing and existing.status in {ApplicationStatus.PENDING, ApplicationStatus.APPROVED}:
        return jsonify({"status": "success", "data": _serialize_application(existing)})

    application = InstructorApplication(user_id=user.id, **{field: payload.get(field) for field in fields})
    db.session.add(application)
    user.instructor_status = ApplicationStatus.PENDING.value
    db.session.commit()
    return jsonify({"status": "success", "data": _serialize_application(application)}), 201


@instructor_applications_bp.route("/<int:application_id>/approve", methods=["PATCH"])
@require_roles(ADMIN)
def approve(application_id):
    return _review(application_id, ApplicationStatus.APPROVED)


@instructor_applications_bp.route("/<int:application_id>/reject", methods=["PATCH"])
@require_roles(ADMIN)
def reject(application_id):
    return _review(application_id, ApplicationStatus.REJECTED)


@instructor_applications_bp.route("/<int:application_id>/revoke", methods=["PATCH"])
@require_roles(ADMIN)
def revoke(application_id):
    return _review(application_id, ApplicationStatus.REVOKED)


def _review(application_id, status):
    application = db.session.get(InstructorApplication, application_id)
    if application is None:
        return _error("Instructor application not found", 404)
    payload = request.get_json(silent=True) or {}
    application.status = status
    application.reviewed_by = current_user().id
    application.reviewed_at = datetime.utcnow()
    if "reason" in payload:
        application.review_reason = payload["reason"]
    application.user.instructor_status = status.value
    if status == ApplicationStatus.APPROVED:
        teacher_role = _role("TEACHER", "Can create and manage instructor-owned courses")
        application.user.role_id = teacher_role.id
    elif status == ApplicationStatus.REVOKED:
        student_role = _role("STUDENT", "Can apply for courses and view resources after approval")
        application.user.role_id = student_role.id
    db.session.commit()
    return jsonify({"status": "success", "data": _serialize_application(application)})


def _serialize_application(application):
    if application is None:
        return None
    return {
        "id": application.id,
        "user_id": application.user_id,
        "user": {
            "id": application.user.id,
            "username": application.user.username,
            "email": application.user.email,
            "full_name": application.user.full_name,
        } if application.user else None,
        "status": application.status.value if application.status else None,
        "qualifications": application.qualifications,
        "expertise": application.expertise,
        "teaching_bio": application.teaching_bio,
        "contact_details": application.contact_details,
        "affiliation": application.affiliation,
        "review_reason": application.review_reason,
        "reviewed_by": application.reviewed_by,
        "reviewed_at": application.reviewed_at.isoformat() if application.reviewed_at else None,
        "created_at": application.created_at.isoformat() if application.created_at else None,
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code


def _role(name, description):
    role = db.session.scalar(select(Role).where(Role.name == name))
    if role is None:
        role = Role(name=name, description=description)
        db.session.add(role)
        db.session.flush()
    return role
