import os
from pathlib import Path

from flask import Blueprint, jsonify, request, url_for

from app.extensions import db
from app.models.media import MediaFile
from app.services.file_service import save_uploaded_file
from app.services.authz import ADMIN, TEACHER, current_user, is_approved_instructor, role_name

uploads_bp = Blueprint("uploads", __name__, url_prefix="/api")


@uploads_bp.route("/uploads", methods=["POST"])
def upload_file():
    user = current_user()
    if user is None:
        return jsonify({"status": "error", "message": "Authentication required. Send Authorization: Bearer <token>"}), 401
    if role_name(user) != ADMIN and not is_approved_instructor(user):
        return jsonify({"status": "error", "message": "Only admin or approved instructors can upload files"}), 403
    uploaded = request.files.get("file")
    if uploaded is None:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    folder = request.form.get("folder", "")
    root = os.getenv("UPLOAD_FOLDER", str(Path(__file__).resolve().parents[2] / "uploads"))

    try:
        result = save_uploaded_file(uploaded, folder=folder, upload_root=root)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"status": "error", "message": f"Upload failed: {exc}"}), 500

    response = {
        "status": "success",
        "filename": result["filename"],
        "stored_name": result["stored_name"],
        "local_path": result["local_path"],
        "absolute_path": result["local_path"],
        "relative_path": result["relative_path"],
        "local_url": result["local_url"],
        "public_url": url_for("uploaded_file", filename=result["relative_path"], _external=True),
        "folder": result["folder"],
        "size": result["size"],
        "mime_type": result["mime_type"],
        "drive_uploaded": result.get("drive_uploaded", False),
    }
    if result.get("drive_url"):
        response["drive_url"] = result["drive_url"]
    if result.get("drive_file_id"):
        response["drive_file_id"] = result["drive_file_id"]
    if result.get("drive_error"):
        response["drive_error"] = result["drive_error"]

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
    db.session.commit()
    response["media_id"] = media_file.id

    return jsonify(response)
