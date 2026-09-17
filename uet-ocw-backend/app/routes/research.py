import os
from datetime import date
from pathlib import Path

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.department import Department
from app.models.media import MediaFile
from app.models.research import ResearchPaper, ResearchStatus
from app.services.authz import ADMIN, current_user, require_roles
from app.services.file_service import save_uploaded_file


research_bp = Blueprint(
    "research_papers",
    __name__,
    url_prefix="/api/research-papers"
)


@research_bp.route("", methods=["GET"])
def get_research_papers():
    try:
        papers = db.session.scalars(
            select(ResearchPaper).order_by(ResearchPaper.display_order, ResearchPaper.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_research_paper(paper) for paper in papers]
    })


@research_bp.route("/department/<int:department_id>", methods=["GET"])
def get_research_by_department(department_id):
    try:
        # Verify department exists
        department = db.session.get(Department, department_id)
        if department is None:
            return _error("Department not found", 404)
        
        papers = db.session.scalars(
            select(ResearchPaper)
            .where(ResearchPaper.department_id == department_id)
            .order_by(ResearchPaper.display_order, ResearchPaper.id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_research_paper(paper) for paper in papers]
    })


@research_bp.route("/<int:research_id>", methods=["GET"])
def get_research_paper(research_id):
    try:
        paper = db.session.get(ResearchPaper, research_id)
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    if paper is None:
        return _error("Research paper not found", 404)

    return jsonify({
        "status": "success",
        "data": _serialize_research_paper(paper)
    })


@research_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_research_paper():
    payload, error = _get_payload()
    if error:
        return error

    upload_error = _attach_uploaded_pdf(payload)
    if upload_error:
        return upload_error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error

    paper = ResearchPaper(**values)
    db.session.add(paper)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected department does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_research_paper(paper)
    }), 201


@research_bp.route("/<int:research_id>", methods=["PUT", "PATCH"])
@require_roles(ADMIN)
def update_research_paper(research_id):
    paper = db.session.get(ResearchPaper, research_id)
    if paper is None:
        return _error("Research paper not found", 404)

    payload, error = _get_payload()
    if error:
        return error

    upload_error = _attach_uploaded_pdf(payload)
    if upload_error:
        return upload_error

    values, error = _validated_values(payload, require_required_fields=False)
    if error:
        return error

    for field, value in values.items():
        setattr(paper, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("The selected department does not exist or the data is invalid", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_research_paper(paper)
    })


@research_bp.route("/<int:research_id>", methods=["DELETE"])
@require_roles(ADMIN)
def delete_research_paper(research_id):
    paper = db.session.get(ResearchPaper, research_id)
    if paper is None:
        return _error("Research paper not found", 404)

    db.session.delete(paper)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Research paper cannot be deleted because it is in use", 409)

    return jsonify({
        "status": "success",
        "message": "Research paper deleted successfully"
    })


_RESEARCH_FIELDS = {
    "department_id",
    "title",
    "abstract",
    "authors",
    "publication_type",
    "journal_name",
    "conference_name",
    "publication_date",
    "publication_year",
    "doi",
    "keywords",
    "paper_url",
    "pdf_url",
    "status",
    "display_order",
}


def _get_payload():
    if request.files or request.form:
        payload = request.form.to_dict()
        return payload, None

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object or multipart form data", 400)
    return payload, None


def _validated_values(payload, require_required_fields):
    values = dict(payload)
    _normalize_research_aliases(values)
    values = {
        field: (None if value == "" else value)
        for field, value in values.items()
    }

    unknown_fields = set(values) - _RESEARCH_FIELDS
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    if require_required_fields:
        required_fields = ["department_id", "title"]
        for field in required_fields:
            if field not in values or values[field] in (None, ""):
                return None, _error(f"{field} is required", 400)

    for integer_field in ["department_id", "publication_year", "display_order"]:
        if integer_field in values:
            values[integer_field] = _optional_int(values[integer_field])

    if "department_id" in values and values["department_id"] is not None:
        if not isinstance(values["department_id"], int) or values["department_id"] <= 0:
            return None, _error("department_id must be a positive integer or null", 400)
        if db.session.get(Department, values["department_id"]) is None:
            return None, _error("Department not found", 404)

    if "title" in values:
        if not isinstance(values["title"], str) or not values["title"].strip():
            return None, _error("title must be a non-empty string", 400)

    if "title" in values:
        values["title"] = values["title"].strip()

    for field_name in [
        "abstract",
        "authors",
        "publication_type",
        "journal_name",
        "conference_name",
        "doi",
        "keywords",
        "paper_url",
        "pdf_url",
    ]:
        if field_name in values and values[field_name] is not None and not isinstance(values[field_name], str):
            return None, _error(f"{field_name} must be a string or null", 400)

    if "publication_year" in values and values["publication_year"] is not None:
        if not isinstance(values["publication_year"], int):
            return None, _error("publication_year must be an integer or null", 400)

    if "publication_date" in values:
        try:
            values["publication_date"] = _optional_date(values["publication_date"])
        except ValueError as exc:
            return None, _error(str(exc), 400)

    if values.get("publication_date") and not values.get("publication_year"):
        values["publication_year"] = values["publication_date"].year

    if "display_order" in values and values["display_order"] is not None:
        if not isinstance(values["display_order"], int):
            return None, _error("display_order must be an integer or null", 400)

    if "status" in values and values["status"] is not None:
        try:
            values["status"] = ResearchStatus(values["status"])
        except (TypeError, ValueError):
            allowed = ", ".join(item.value for item in ResearchStatus)
            return None, _error(f"status must be one of: {allowed}", 400)

    return values, None


def _attach_uploaded_pdf(payload):
    uploaded = request.files.get("pdf_file") or request.files.get("paper_file")
    if uploaded is None or not uploaded.filename:
        return None
    if not _is_pdf_upload(uploaded):
        return _error("Uploaded research paper must be a PDF file", 400)

    root = os.getenv("UPLOAD_FOLDER", str(Path(__file__).resolve().parents[2] / "uploads"))
    try:
        result = save_uploaded_file(uploaded, folder="research/papers", upload_root=root)
    except ValueError as exc:
        return _error(str(exc), 400)
    except Exception as exc:
        return _error(f"Upload failed: {exc}", 500)

    payload["pdf_url"] = result["local_url"]

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


def _is_pdf_upload(uploaded):
    filename = (uploaded.filename or "").lower()
    mimetype = (uploaded.mimetype or "").lower()
    return filename.endswith(".pdf") or mimetype == "application/pdf"


def _normalize_research_aliases(values):
    publication_title = values.pop("publication_title", None)
    if publication_title:
        publication_type = str(values.get("publication_type") or "").strip().lower()
        if publication_type == "conference":
            values["conference_name"] = publication_title
            values.setdefault("journal_name", None)
        else:
            values["journal_name"] = publication_title
            values.setdefault("conference_name", None)


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
            raise ValueError("publication_date must be a valid YYYY-MM-DD date")
    return value


def _serialize_research_paper(paper):
    department = paper.department
    return {
        "id": paper.id,
        "department_id": paper.department_id,
        "department": _serialize_department(department) if department else None,
        "title": paper.title,
        "abstract": paper.abstract,
        "authors": paper.authors,
        "publication_type": paper.publication_type,
        "journal_name": paper.journal_name,
        "conference_name": paper.conference_name,
        "publication_date": paper.publication_date.isoformat() if paper.publication_date else None,
        "publication_year": paper.publication_year,
        "doi": paper.doi,
        "keywords": paper.keywords,
        "paper_url": paper.paper_url,
        "pdf_url": paper.pdf_url,
        "status": paper.status.value if paper.status is not None else None,
        "display_order": paper.display_order,
        "created_at": paper.created_at.isoformat() if paper.created_at else None,
        "updated_at": paper.updated_at.isoformat() if paper.updated_at else None,
    }


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
