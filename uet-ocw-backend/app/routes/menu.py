from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.menu import MenuItem, MenuLocation
from app.services.authz import ADMIN, require_roles

menu_bp = Blueprint(
    "menu",
    __name__,
    url_prefix="/api/menu"
)


@menu_bp.route("", methods=["GET"])
def get_menu_items():
    try:
        items = db.session.scalars(
            select(MenuItem).order_by(MenuItem.display_order, MenuItem.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_menu_item(item) for item in items]
    })


@menu_bp.route("/<int:menu_id>", methods=["GET"])
def get_menu_item(menu_id):
    try:
        menu_item = db.session.get(MenuItem, menu_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    if menu_item is None:
        return _error("Menu item not found", 404)

    return jsonify({
        "status": "success",
        "data": _serialize_menu_item(menu_item)
    })


@menu_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_menu_item():
    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error

    menu_item = MenuItem(**values)
    db.session.add(menu_item)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Menu item could not be created", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_menu_item(menu_item)
    }), 201


@menu_bp.route("/<int:menu_id>", methods=["PUT", "PATCH"])
@require_roles(ADMIN)
def update_menu_item(menu_id):
    menu_item = db.session.get(MenuItem, menu_id)
    if menu_item is None:
        return _error("Menu item not found", 404)

    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=False)
    if error:
        return error

    for field, value in values.items():
        setattr(menu_item, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Menu item could not be updated", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_menu_item(menu_item)
    })


@menu_bp.route("/<int:menu_id>", methods=["DELETE"])
@require_roles(ADMIN)
def delete_menu_item(menu_id):
    menu_item = db.session.get(MenuItem, menu_id)
    if menu_item is None:
        return _error("Menu item not found", 404)

    db.session.delete(menu_item)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Menu item cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Menu item deleted successfully"
    })


_MENU_FIELDS = {
    "parent_id",
    "title",
    "slug",
    "url",
    "menu_location",
    "icon",
    "display_order",
    "is_active",
}


def _get_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object", 400)
    return payload, None


def _validated_values(payload, require_required_fields):
    unknown_fields = set(payload) - _MENU_FIELDS
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    if require_required_fields and "title" not in payload:
        return None, _error("title is required", 400)

    if "title" in payload:
        if not isinstance(payload["title"], str) or not payload["title"].strip():
            return None, _error("title must be a non-empty string", 400)

    if "slug" in payload and payload["slug"] is not None and (not isinstance(payload["slug"], str) or not payload["slug"].strip()):
        return None, _error("slug must be a non-empty string or null", 400)

    if "url" in payload and payload["url"] is not None and (not isinstance(payload["url"], str) or not payload["url"].strip()):
        return None, _error("url must be a non-empty string or null", 400)

    if "menu_location" in payload and payload["menu_location"] is not None:
        if isinstance(payload["menu_location"], str):
            try:
                payload["menu_location"] = MenuLocation(payload["menu_location"].upper())
            except ValueError:
                return None, _error("menu_location must be one of HEADER, FOOTER, SIDEBAR", 400)
        elif not isinstance(payload["menu_location"], MenuLocation):
            return None, _error("menu_location must be a valid MenuLocation value", 400)

    if "parent_id" in payload and payload["parent_id"] is not None and not isinstance(payload["parent_id"], int):
        return None, _error("parent_id must be an integer or null", 400)

    if "display_order" in payload and payload["display_order"] is not None and not isinstance(payload["display_order"], int):
        return None, _error("display_order must be an integer or null", 400)

    if "is_active" in payload and payload["is_active"] is not None and not isinstance(payload["is_active"], bool):
        return None, _error("is_active must be a boolean or null", 400)

    values = dict(payload)
    if "title" in values:
        values["title"] = values["title"].strip()
    if "slug" in values and values["slug"] is not None:
        values["slug"] = values["slug"].strip()
    if "url" in values and values["url"] is not None:
        values["url"] = values["url"].strip()
    if "icon" in values and values["icon"] is not None:
        values["icon"] = values["icon"].strip()

    return values, None


def _serialize_menu_item(item):
    return {
        "id": item.id,
        "parent_id": item.parent_id,
        "title": item.title,
        "slug": item.slug,
        "url": item.url,
        "menu_location": item.menu_location.value if isinstance(item.menu_location, MenuLocation) else item.menu_location,
        "icon": item.icon,
        "display_order": item.display_order,
        "is_active": item.is_active,
        "children": [_serialize_menu_item(child) for child in sorted(item.children, key=lambda child: child.display_order or 0)],
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
