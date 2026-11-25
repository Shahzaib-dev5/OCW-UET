import os
from datetime import date
from pathlib import Path

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.department import Department
from app.models.invited_talk import InvitedTalk, InvitedTalkResource, InvitedTalkStatus
from app.models.media import MediaFile
from app.services.authz import current_user, is_admin, is_approved_instructor, is_course_reviewer
from app.services.file_service import save_uploaded_file


invited_talks_bp = Blueprint(
    "invited_talks",
    __name__,
    url_prefix="/api/invited-talks"
)


@invited_talks_bp.route("", methods=["GET"])
def get_invited_talks():
    try:
        talks = db.session.scalars(
            _visible_talks_query().order_by(InvitedTalk.display_order, InvitedTalk.talk_date.desc(), InvitedTalk.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_invited_talk(talk) for talk in talks]
    })


@invited_talks_bp.route("/department/<int:department_id>", methods=["GET"])
def get_invited_talks_by_department(department_id):
    try:
        department = db.session.get(Department, department_id)
        if department is None:
            return _error("Department not found", 404)

        talks = db.session.scalars(
            _visible_talks_query()
            .where(InvitedTalk.department_id == department_id)
            .order_by(InvitedTalk.display_order, InvitedTalk.talk_date.desc(), InvitedTalk.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_invited_talk(talk) for talk in talks]
    })


@invited_talks_bp.route("/<int:talk_id>", methods=["GET"])
def get_invited_talk(talk_id):
    try:
        talk = db.session.get(InvitedTalk, talk_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    if talk is None:
        return _error("Invited talk not found", 404)
    if not _can_view_talk(talk):
        return _error("Invited talk is awaiting admin approval", 404)

    return jsonify({
        "status": "success",
        "data": _serialize_invited_talk(talk)
    })


@invited_talks_bp.route("", methods=["POST"])
def create_invited_talk():
    user = current_user()
    if user is None:
        return _error("Authentication required. Send Authorization: Bearer <token>", 401)
    if not is_admin(user) and not is_approved_instructor(user):
        return _error("Only admin or approved instructors can create invited talks", 403)
    payload, error = _get_payload()
    if error:
        return error

    upload_error = _attach_uploaded_file(payload)
    if upload_error:
        return upload_error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error

    if not is_admin(user):
        values["owner_id"] = user.id
        values["status"] = InvitedTalkStatus.DRAFT
    talk = InvitedTalk(**values)
    if is_admin(user) and talk.status == InvitedTalkStatus.PUBLISHED:
        talk.review_status = "APPROVED"
    db.session.add(talk)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected department does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_invited_talk(talk)
    }), 201


@invited_talks_bp.route("/<int:talk_id>", methods=["PUT", "PATCH"])
def update_invited_talk(talk_id):
    talk = db.session.get(InvitedTalk, talk_id)
    if talk is None:
        return _error("Invited talk not found", 404)
    if not _can_manage_talk(talk):
        return _error("Only admin or the approved talk owner can update this invited talk", 403)

    payload, error = _get_payload()
    if error:
        return error
    upload_error = _attach_uploaded_file(payload)
    if upload_error:
        return upload_error

    values, error = _validated_values(payload, require_required_fields=False)
    if error:
        return error
    if not is_admin(current_user()):
        values["status"] = InvitedTalkStatus.DRAFT
        talk.review_status = "PENDING"

    for field, value in values.items():
        setattr(talk, field, value)
    if is_admin(current_user()) and "status" in values:
        talk.review_status = "APPROVED" if talk.status == InvitedTalkStatus.PUBLISHED else "PENDING"

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected department does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_invited_talk(talk)
    })


@invited_talks_bp.route("/<int:talk_id>", methods=["DELETE"])
def delete_invited_talk(talk_id):
    talk = db.session.get(InvitedTalk, talk_id)
    if talk is None:
        return _error("Invited talk not found", 404)
    if not _can_manage_talk(talk):
        return _error("Only admin or the approved talk owner can delete this invited talk", 403)

    db.session.delete(talk)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Invited talk cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Invited talk deleted successfully"
    })


@invited_talks_bp.route("/<int:talk_id>/resources", methods=["GET"])
def get_invited_talk_resources(talk_id):
    talk = db.session.get(InvitedTalk, talk_id)
    if talk is None or not _can_view_talk(talk):
        return _error("Invited talk not found", 404)
    return jsonify(status="success", data=[_serialize_resource(item) for item in talk.resources])


@invited_talks_bp.route("/<int:talk_id>/resources", methods=["POST"])
def create_invited_talk_resource(talk_id):
    talk = db.session.get(InvitedTalk, talk_id)
    if talk is None:
        return _error("Invited talk not found", 404)
    if not _can_manage_talk(talk):
        return _error("Only admin or the approved talk owner can add resources", 403)
    values, error = _validated_resource_values(request.get_json(silent=True), True)
    if error:
        return error
    resource = InvitedTalkResource(talk_id=talk.id, **values)
    db.session.add(resource)
    db.session.commit()
    return jsonify(status="success", data=_serialize_resource(resource)), 201


@invited_talks_bp.route("/resources/<int:resource_id>", methods=["PATCH", "PUT"])
def update_invited_talk_resource(resource_id):
    resource = db.session.get(InvitedTalkResource, resource_id)
    if resource is None:
        return _error("Talk resource not found", 404)
    if not _can_manage_talk(resource.talk):
        return _error("Only admin or the approved talk owner can update resources", 403)
    values, error = _validated_resource_values(request.get_json(silent=True), False)
    if error:
        return error
    for field, value in values.items():
        setattr(resource, field, value)
    db.session.commit()
    return jsonify(status="success", data=_serialize_resource(resource))


@invited_talks_bp.route("/resources/<int:resource_id>", methods=["DELETE"])
def delete_invited_talk_resource(resource_id):
    resource = db.session.get(InvitedTalkResource, resource_id)
    if resource is None:
        return _error("Talk resource not found", 404)
    if not _can_manage_talk(resource.talk):
        return _error("Only admin or the approved talk owner can delete resources", 403)
    db.session.delete(resource)
    db.session.commit()
    return jsonify(status="success", message="Talk resource deleted successfully")


_INVITED_TALK_FIELDS = {
    "department_id",
    "talk_title",
    "event_title",
    "presenter",
    "talk_date",
    "date",
    "video_url",
    "video_upload_link",
    "upload_url",
    "publication",
    "status",
    "display_order",
}


def _get_payload():
    if request.files or request.form:
        return request.form.to_dict(), None

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object or multipart form data", 400)
    return payload, None


def _validated_values(payload, require_required_fields):
    values = dict(payload)
    _normalize_aliases(values)
    values = {
        field: (None if value == "" else value)
        for field, value in values.items()
    }

    unknown_fields = set(values) - (_INVITED_TALK_FIELDS - {"date", "video_upload_link"})
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    if require_required_fields:
        required_fields = ["department_id", "talk_title"]
        for field in required_fields:
            if field not in values or values[field] in (None, ""):
                return None, _error(f"{field} is required", 400)

    for integer_field in ["department_id", "display_order"]:
        if integer_field in values:
            values[integer_field] = _optional_int(values[integer_field])

    if "department_id" in values and values["department_id"] is not None:
        if not isinstance(values["department_id"], int) or values["department_id"] <= 0:
            return None, _error("department_id must be a positive integer or null", 400)
        if db.session.get(Department, values["department_id"]) is None:
            return None, _error("Department not found", 404)

    if "talk_title" in values:
        if not isinstance(values["talk_title"], str) or not values["talk_title"].strip():
            return None, _error("talk_title must be a non-empty string", 400)
        values["talk_title"] = values["talk_title"].strip()

    for field_name in ["event_title", "presenter", "video_url", "upload_url", "publication"]:
        if field_name in values and values[field_name] is not None and not isinstance(values[field_name], str):
            return None, _error(f"{field_name} must be a string or null", 400)

    if "talk_date" in values:
        try:
            values["talk_date"] = _optional_date(values["talk_date"])
        except ValueError as exc:
            return None, _error(str(exc), 400)

    if "display_order" in values and values["display_order"] is not None:
        if not isinstance(values["display_order"], int):
            return None, _error("display_order must be an integer or null", 400)

    if "status" in values and values["status"] is not None:
        try:
            values["status"] = InvitedTalkStatus(values["status"])
        except (TypeError, ValueError):
            allowed = ", ".join(item.value for item in InvitedTalkStatus)
            return None, _error(f"status must be one of: {allowed}", 400)

    return values, None


def _attach_uploaded_file(payload):
    uploaded = request.files.get("upload_file") or request.files.get("file") or request.files.get("attachment")
    if uploaded is None or not uploaded.filename:
        return None

    root = os.getenv("UPLOAD_FOLDER", str(Path(__file__).resolve().parents[2] / "uploads"))
    try:
        result = save_uploaded_file(uploaded, folder="invited-talks", upload_root=root)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Upload failed: {exc}", 500)

    payload["upload_url"] = result["local_url"]

    user = current_user()
    media_file = MediaFile(
        original_name=uploaded.filename,
        stored_name=result["stored_name"],
        file_path=result["local_path"],
        file_url=result["local_url"],
        mime_type=result["mime_type"],
        file_size=result["size"],
        uploaded_by=user.id if user else None,
    )
    db.session.add(media_file)
    return None


def _normalize_aliases(values):
    if "date" in values and "talk_date" not in values:
        values["talk_date"] = values.pop("date")
    else:
        values.pop("date", None)

    if "video_upload_link" in values and "video_url" not in values:
        values["video_url"] = values.pop("video_upload_link")
    else:
        values.pop("video_upload_link", None)


def _optional_int(value):
    if value in ("", None):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _optional_date(value):
    if value in ("", None):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValueError("talk_date must be a valid YYYY-MM-DD date")
    return value


def _serialize_invited_talk(talk):
    department = talk.department
    return {
        "id": talk.id,
        "department_id": talk.department_id,
        "owner_id": talk.owner_id,
        "department": _serialize_department(department) if department else None,
        "talk_title": talk.talk_title,
        "event_title": talk.event_title,
        "presenter": talk.presenter,
        "talk_date": talk.talk_date.isoformat() if talk.talk_date else None,
        "date": talk.talk_date.isoformat() if talk.talk_date else None,
        "video_url": talk.video_url,
        "video_upload_link": talk.video_url,
        "upload_url": talk.upload_url,
        "publication": talk.publication,
        "status": talk.status.value if talk.status is not None else None,
        "display_order": talk.display_order,
        "review_status": talk.review_status,
        "can_manage": _can_manage_talk(talk),
        "resources": [_serialize_resource(item) for item in talk.resources],
        "created_at": talk.created_at.isoformat() if talk.created_at else None,
        "updated_at": talk.updated_at.isoformat() if talk.updated_at else None,
    }


def _validated_resource_values(payload, require_required_fields):
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object", 400)
    allowed = {"title", "resource_type", "url", "description", "display_order"}
    unknown = set(payload) - allowed
    if unknown:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown))}", 400)
    if require_required_fields:
        for field in ("title", "url"):
            if not str(payload.get(field) or "").strip():
                return None, _error(f"{field} is required", 400)
    values = dict(payload)
    for field in ("title", "url"):
        if field in values:
            if not isinstance(values[field], str) or not values[field].strip():
                return None, _error(f"{field} must be a non-empty string", 400)
            values[field] = values[field].strip()
    if "resource_type" in values:
        values["resource_type"] = str(values["resource_type"]).upper()
        if values["resource_type"] not in {"VIDEO", "FILE", "LINK", "SLIDES", "DOCUMENT"}:
            return None, _error("resource_type must be VIDEO, FILE, LINK, SLIDES, or DOCUMENT", 400)
    if "display_order" in values:
        try:
            values["display_order"] = int(values["display_order"] or 0)
        except (TypeError, ValueError):
            return None, _error("display_order must be an integer", 400)
    if "description" in values and values["description"] is not None and not isinstance(values["description"], str):
        return None, _error("description must be a string or null", 400)
    return values, None


def _serialize_resource(resource):
    return {
        "id": resource.id, "talk_id": resource.talk_id, "title": resource.title,
        "resource_type": resource.resource_type, "url": resource.url,
        "description": resource.description, "display_order": resource.display_order,
        "created_at": resource.created_at.isoformat() if resource.created_at else None,
        "updated_at": resource.updated_at.isoformat() if resource.updated_at else None,
    }


def _visible_talks_query():
    query = select(InvitedTalk)
    user = current_user()
    if user is not None and is_course_reviewer(user):
        return query
    if user is not None and is_approved_instructor(user):
        return query.where(
            (InvitedTalk.status == InvitedTalkStatus.PUBLISHED) | (InvitedTalk.owner_id == user.id)
        )
    return query.where(InvitedTalk.status == InvitedTalkStatus.PUBLISHED)


def _can_manage_talk(talk):
    user = current_user()
    return bool(user and (is_admin(user) or (is_approved_instructor(user) and talk.owner_id == user.id)))


def _can_view_talk(talk):
    return talk.status == InvitedTalkStatus.PUBLISHED or _can_manage_talk(talk) or is_course_reviewer()


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
