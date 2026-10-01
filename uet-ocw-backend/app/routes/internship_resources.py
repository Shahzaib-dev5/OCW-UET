import os
from pathlib import Path

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.internship import Internship
from app.models.internship_resource import InternshipResource, InternshipResourceType
from app.services.authz import ADMIN, require_roles
from app.services.file_service import save_uploaded_file


internship_resources_bp = Blueprint(
    "internship_resources",
    __name__,
    url_prefix="/api/internship-resources"
)

skills_development_resources_bp = Blueprint(
    "skills_development_resources",
    __name__,
    url_prefix="/api/skills-development-resources"
)

@skills_development_resources_bp.route("", methods=["GET"])
@internship_resources_bp.route("", methods=["GET"])
def get_internship_resources():
    try:
        resources = db.session.scalars(
            select(InternshipResource).order_by(InternshipResource.display_order, InternshipResource.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_resource(resource) for resource in resources]
    })


@skills_development_resources_bp.route("/skills-development/<int:internship_id>", methods=["GET"])
@internship_resources_bp.route("/internship/<int:internship_id>", methods=["GET"])
def get_resources_by_internship(internship_id):
    try:
        internship = db.session.get(Internship, internship_id)
        if internship is None:
            return _error("Skills development program not found", 404)

        resources = db.session.scalars(
            select(InternshipResource)
            .where(InternshipResource.internship_id == internship_id)
            .order_by(InternshipResource.display_order, InternshipResource.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_resource(resource) for resource in resources]
    })


@skills_development_resources_bp.route("/<int:resource_id>", methods=["GET"])
@internship_resources_bp.route("/<int:resource_id>", methods=["GET"])
def get_internship_resource(resource_id):
    try:
        resource = db.session.get(InternshipResource, resource_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    if resource is None:
        return _error("Skills development resource not found", 404)

    return jsonify({
        "status": "success",
        "data": _serialize_resource(resource)
    })


@skills_development_resources_bp.route("", methods=["POST"])
@internship_resources_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_internship_resource():
    payload, uploaded_file, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error
    upload_result, error = _save_resource_file(uploaded_file, values["internship_id"])
    if error:
        return error
    if upload_result:
        values.update(_resource_file_values(upload_result))

    resource = InternshipResource(**values)
    db.session.add(resource)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected skills development program does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_resource(resource)
    }), 201


@skills_development_resources_bp.route("/<int:resource_id>", methods=["PUT", "PATCH"])
@internship_resources_bp.route("/<int:resource_id>", methods=["PUT", "PATCH"])
@require_roles(ADMIN)
def update_internship_resource(resource_id):
    resource = db.session.get(InternshipResource, resource_id)
    if resource is None:
        return _error("Skills development resource not found", 404)

    payload, uploaded_file, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=False)
    if error:
        return error
    target_internship_id = values.get("internship_id", resource.internship_id)
    upload_result, error = _save_resource_file(uploaded_file, target_internship_id)
    if error:
        return error
    if upload_result:
        values.update(_resource_file_values(upload_result))

    for field, value in values.items():
        setattr(resource, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected skills development program does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_resource(resource)
    })


@skills_development_resources_bp.route("/<int:resource_id>", methods=["DELETE"])
@internship_resources_bp.route("/<int:resource_id>", methods=["DELETE"])
@require_roles(ADMIN)
def delete_internship_resource(resource_id):
    resource = db.session.get(InternshipResource, resource_id)
    if resource is None:
        return _error("Skills development resource not found", 404)

    db.session.delete(resource)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Skills development resource cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Skills development resource deleted successfully"
    })


_INTERNSHIP_RESOURCE_FIELDS = {
    "internship_id",
    "title",
    "resource_type",
    "description",
    "file_url",
    "external_url",
    "file_size",
    "mime_type",
    "display_order",
    "is_active",
}


def _get_payload():
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        payload = dict(request.form)
        uploaded_file = request.files.get("file")
        return payload, uploaded_file, None

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, None, _error("Request body must be a JSON object or multipart/form-data", 400)
    return payload, None, None


def _validated_values(payload, require_required_fields):
    unknown_fields = set(payload) - _INTERNSHIP_RESOURCE_FIELDS
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    if require_required_fields:
        required_fields = ["internship_id", "title", "resource_type"]
        for field in required_fields:
            if field not in payload:
                return None, _error(f"{field} is required", 400)

    values = dict(payload)

    for integer_field in ["internship_id", "file_size", "display_order"]:
        if integer_field in values and values[integer_field] in {"", None}:
            values[integer_field] = None
        elif integer_field in values and isinstance(values[integer_field], str):
            try:
                values[integer_field] = int(values[integer_field])
            except ValueError:
                return None, _error(f"{integer_field} must be an integer or null", 400)

    if "is_active" in values and isinstance(values["is_active"], str):
        normalized = values["is_active"].strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            values["is_active"] = True
        elif normalized in {"0", "false", "no", "off"}:
            values["is_active"] = False
        elif normalized == "":
            values["is_active"] = None
        else:
            return None, _error("is_active must be a boolean or null", 400)

    if "internship_id" in values and values["internship_id"] is not None:
        if not isinstance(values["internship_id"], int) or values["internship_id"] <= 0:
            return None, _error("internship_id must be a positive integer or null", 400)
        if db.session.get(Internship, values["internship_id"]) is None:
            return None, _error("Skills development program not found", 404)

    if "title" in values:
        if not isinstance(values["title"], str) or not values["title"].strip():
            return None, _error("title must be a non-empty string", 400)

    if "title" in values:
        values["title"] = values["title"].strip()

    for field_name in ["description", "file_url", "external_url", "mime_type"]:
        if field_name in values and values[field_name] is not None and not isinstance(values[field_name], str):
            return None, _error(f"{field_name} must be a string or null", 400)
        if field_name in values and values[field_name] == "":
            values[field_name] = None

    if "resource_type" in values and values["resource_type"] is not None:
        try:
            values["resource_type"] = InternshipResourceType(str(values["resource_type"]).upper())
        except (TypeError, ValueError):
            allowed = ", ".join(item.value for item in InternshipResourceType)
            return None, _error(f"resource_type must be one of: {allowed}", 400)

    if "file_size" in values and values["file_size"] is not None:
        if not isinstance(values["file_size"], int) or values["file_size"] < 0:
            return None, _error("file_size must be a non-negative integer or null", 400)

    if "display_order" in values and values["display_order"] is not None:
        if not isinstance(values["display_order"], int):
            return None, _error("display_order must be an integer or null", 400)

    if "is_active" in values and values["is_active"] is not None:
        if not isinstance(values["is_active"], bool):
            return None, _error("is_active must be a boolean or null", 400)

    return values, None


def _save_resource_file(uploaded_file, internship_id):
    if uploaded_file is None or not getattr(uploaded_file, "filename", None):
        return None, None

    upload_root = os.getenv("UPLOAD_FOLDER", str(Path(__file__).resolve().parents[2] / "uploads"))
    folder = f"internships/{internship_id}/resources"
    try:
        return save_uploaded_file(uploaded_file, folder=folder, upload_root=upload_root), None
    except ValueError as exc:
        return None, _error(str(exc), 400)
    except OSError:
        return None, _error("Unable to save uploaded skills development resource file", 500)


def _resource_file_values(upload_result):
    return {
        "file_url": upload_result["local_url"],
        "file_size": upload_result["size"],
        "mime_type": upload_result["mime_type"],
    }


def _serialize_resource(resource):
    return {
        "id": resource.id,
        "internship_id": resource.internship_id,
        "internship": _serialize_internship(resource.internship) if resource.internship else None,
        "title": resource.title,
        "resource_type": resource.resource_type.value if resource.resource_type else None,
        "description": resource.description,
        "file_url": resource.file_url,
        "external_url": resource.external_url,
        "file_size": resource.file_size,
        "mime_type": resource.mime_type,
        "display_order": resource.display_order,
        "is_active": resource.is_active,
        "created_at": resource.created_at.isoformat() if resource.created_at else None,
        "updated_at": resource.updated_at.isoformat() if resource.updated_at else None,
    }


def _serialize_internship(internship):
    return {
        "id": internship.id,
        "department_id": internship.department_id,
        "title": internship.title,
        "slug": internship.slug,
        "status": internship.status.value if internship.status else None,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
