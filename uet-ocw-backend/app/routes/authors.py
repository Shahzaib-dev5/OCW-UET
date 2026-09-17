from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.author import Author
from app.services.authz import ADMIN, require_roles


authors_bp = Blueprint(
    "authors",
    __name__,
    url_prefix="/api/authors"
)


@authors_bp.route("", methods=["GET"])
def get_authors():
    try:
        authors = db.session.scalars(
            select(Author).order_by(Author.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_author(author) for author in authors]
    })


@authors_bp.route("/<int:author_id>", methods=["GET"])
def get_author(author_id):
    try:
        author = db.session.get(Author, author_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    if author is None:
        return _error("Author not found", 404)

    return jsonify({
        "status": "success",
        "data": _serialize_author(author)
    })


@authors_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_author():
    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error

    author = Author(**values)
    db.session.add(author)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Author could not be created", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_author(author)
    }), 201


@authors_bp.route("/<int:author_id>", methods=["PUT", "PATCH"])
@require_roles(ADMIN)
def update_author(author_id):
    author = db.session.get(Author, author_id)
    if author is None:
        return _error("Author not found", 404)

    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=False)
    if error:
        return error

    for field, value in values.items():
        setattr(author, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Author could not be updated", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_author(author)
    })


@authors_bp.route("/<int:author_id>", methods=["DELETE"])
@require_roles(ADMIN)
def delete_author(author_id):
    author = db.session.get(Author, author_id)
    if author is None:
        return _error("Author not found", 404)

    db.session.delete(author)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Author cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Author deleted successfully"
    })


_AUTHOR_FIELDS = {
    "name",
    "affiliation",
    "email",
    "profile_url",
}


def _get_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object", 400)
    return payload, None


def _validated_values(payload, require_required_fields):
    unknown_fields = set(payload) - _AUTHOR_FIELDS
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    if require_required_fields and "name" not in payload:
        return None, _error("name is required", 400)

    if "name" in payload:
        if not isinstance(payload["name"], str) or not payload["name"].strip():
            return None, _error("name must be a non-empty string", 400)

    values = dict(payload)
    if "name" in values:
        values["name"] = values["name"].strip()

    for field_name in ["affiliation", "email", "profile_url"]:
        if field_name in values and values[field_name] is not None and not isinstance(values[field_name], str):
            return None, _error(f"{field_name} must be a string or null", 400)

    return values, None


def _serialize_author(author):
    return {
        "id": author.id,
        "name": author.name,
        "affiliation": author.affiliation,
        "email": author.email,
        "profile_url": author.profile_url,
        "created_at": author.created_at.isoformat() if author.created_at else None,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
