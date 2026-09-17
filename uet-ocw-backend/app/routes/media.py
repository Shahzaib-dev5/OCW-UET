from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.media import MediaFile
from app.services.authz import ADMIN, current_user, require_roles


media_bp = Blueprint(
    "media",
    __name__,
    url_prefix="/api/media"
)


@media_bp.route("", methods=["GET"])
def get_media_files():
    try:
        media_files = db.session.scalars(
            select(MediaFile).order_by(MediaFile.created_at.desc())
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_media_file(media_file) for media_file in media_files]
    })


@media_bp.route("/<int:media_id>", methods=["GET"])
def get_media_file(media_id):
    try:
        media_file = db.session.get(MediaFile, media_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    if media_file is None:
        return _error("Media file not found", 404)

    return jsonify({
        "status": "success",
        "data": _serialize_media_file(media_file)
    })


@media_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_media_file():
    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error

    if "uploaded_by" not in values or values["uploaded_by"] is None:
        values["uploaded_by"] = current_user().id

    media_file = MediaFile(**values)
    db.session.add(media_file)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Media file could not be created", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_media_file(media_file)
    }), 201


@media_bp.route("/<int:media_id>", methods=["PUT", "PATCH"])
@require_roles(ADMIN)
def update_media_file(media_id):
    media_file = db.session.get(MediaFile, media_id)
    if media_file is None:
        return _error("Media file not found", 404)

    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=False)
    if error:
        return error

    for field, value in values.items():
        setattr(media_file, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Media file could not be updated", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_media_file(media_file)
    })


@media_bp.route("/<int:media_id>", methods=["DELETE"])
@require_roles(ADMIN)
def delete_media_file(media_id):
    media_file = db.session.get(MediaFile, media_id)
    if media_file is None:
        return _error("Media file not found", 404)

    db.session.delete(media_file)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Media file cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Media file deleted successfully"
    })


_MEDIA_FIELDS = {
    "original_name",
    "stored_name",
    "file_path",
    "file_url",
    "mime_type",
    "file_size",
    "uploaded_by",
}


def _get_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object", 400)
    return payload, None


def _validated_values(payload, require_required_fields):
    unknown_fields = set(payload) - _MEDIA_FIELDS
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    if require_required_fields and "original_name" not in payload:
        return None, _error("original_name is required", 400)

    if "original_name" in payload:
        if not isinstance(payload["original_name"], str) or not payload["original_name"].strip():
            return None, _error("original_name must be a non-empty string", 400)

    if "stored_name" in payload and payload["stored_name"] is not None and (not isinstance(payload["stored_name"], str) or not payload["stored_name"].strip()):
        return None, _error("stored_name must be a non-empty string or null", 400)

    if "file_path" in payload and payload["file_path"] is not None and (not isinstance(payload["file_path"], str) or not payload["file_path"].strip()):
        return None, _error("file_path must be a non-empty string or null", 400)

    if "file_url" in payload and payload["file_url"] is not None and (not isinstance(payload["file_url"], str) or not payload["file_url"].strip()):
        return None, _error("file_url must be a non-empty string or null", 400)

    if "mime_type" in payload and payload["mime_type"] is not None and (not isinstance(payload["mime_type"], str) or not payload["mime_type"].strip()):
        return None, _error("mime_type must be a non-empty string or null", 400)

    if "file_size" in payload and payload["file_size"] is not None and not isinstance(payload["file_size"], int):
        return None, _error("file_size must be an integer or null", 400)

    if "uploaded_by" in payload and payload["uploaded_by"] is not None and not isinstance(payload["uploaded_by"], int):
        return None, _error("uploaded_by must be an integer or null", 400)

    values = dict(payload)
    if "original_name" in values:
        values["original_name"] = values["original_name"].strip()
    if "stored_name" in values and values["stored_name"] is not None:
        values["stored_name"] = values["stored_name"].strip()
    if "file_path" in values and values["file_path"] is not None:
        values["file_path"] = values["file_path"].strip()
    if "file_url" in values and values["file_url"] is not None:
        values["file_url"] = values["file_url"].strip()
    if "mime_type" in values and values["mime_type"] is not None:
        values["mime_type"] = values["mime_type"].strip()

    return values, None


def _serialize_media_file(media_file):
    return {
        "id": media_file.id,
        "original_name": media_file.original_name,
        "stored_name": media_file.stored_name,
        "file_path": media_file.file_path,
        "file_url": media_file.file_url,
        "mime_type": media_file.mime_type,
        "file_size": media_file.file_size,
        "uploaded_by": media_file.uploaded_by,
        "created_at": media_file.created_at.isoformat() if media_file.created_at else None,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
