from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.extensions import db
from app.models.author import Author
from app.models.research import ResearchPaper, ResearchPaperAuthor
from app.services.authz import ADMIN, require_roles


research_authors_bp = Blueprint(
    "research_paper_authors",
    __name__,
    url_prefix="/api/research-paper-authors"
)


@research_authors_bp.route("", methods=["GET"])
def get_research_authors():
    try:
        links = db.session.scalars(
            select(ResearchPaperAuthor).order_by(ResearchPaperAuthor.author_order, ResearchPaperAuthor.research_paper_id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_link(link) for link in links]
    })


@research_authors_bp.route("/paper/<int:research_paper_id>", methods=["GET"])
def get_authors_for_paper(research_paper_id):
    try:
        paper = db.session.get(ResearchPaper, research_paper_id)
        if paper is None:
            return _error("Research paper not found", 404)

        links = db.session.scalars(
            select(ResearchPaperAuthor)
            .where(ResearchPaperAuthor.research_paper_id == research_paper_id)
            .order_by(ResearchPaperAuthor.author_order, ResearchPaperAuthor.author_id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_link(link) for link in links]
    })


@research_authors_bp.route("/author/<int:author_id>", methods=["GET"])
def get_papers_for_author(author_id):
    try:
        author = db.session.get(Author, author_id)
        if author is None:
            return _error("Author not found", 404)

        links = db.session.scalars(
            select(ResearchPaperAuthor)
            .where(ResearchPaperAuthor.author_id == author_id)
            .order_by(ResearchPaperAuthor.author_order, ResearchPaperAuthor.research_paper_id)
        ).all()
    except OperationalError:
        db.session.rollback()
        return _error("Database is unavailable. Check your database settings", 503)

    return jsonify({
        "status": "success",
        "data": [_serialize_link(link) for link in links]
    })


@research_authors_bp.route("", methods=["POST"])
@require_roles(ADMIN)
def create_research_author_link():
    payload, error = _get_payload()
    if error:
        return error

    values, error = _validated_values(payload, require_required_fields=True)
    if error:
        return error

    link = ResearchPaperAuthor(**values)
    db.session.add(link)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Research paper and author relationship is invalid or already exists", 400)

    return jsonify({
        "status": "success",
        "data": _serialize_link(link)
    }), 201


@research_authors_bp.route("/paper/<int:research_paper_id>/author/<int:author_id>", methods=["DELETE"])
@require_roles(ADMIN)
def delete_research_author_link(research_paper_id, author_id):
    link = db.session.get(ResearchPaperAuthor, (research_paper_id, author_id))
    if link is None:
        return _error("Research paper author link not found", 404)

    db.session.delete(link)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Research paper author link could not be deleted", 409)

    return jsonify({
        "status": "success",
        "message": "Research paper author link deleted successfully"
    })


_RESEARCH_AUTHOR_FIELDS = {
    "research_paper_id",
    "author_id",
    "author_order",
}


def _get_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _error("Request body must be a JSON object", 400)
    return payload, None


def _validated_values(payload, require_required_fields):
    unknown_fields = set(payload) - _RESEARCH_AUTHOR_FIELDS
    if unknown_fields:
        return None, _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    if require_required_fields:
        required_fields = ["research_paper_id", "author_id"]
        for field in required_fields:
            if field not in payload:
                return None, _error(f"{field} is required", 400)

    if "research_paper_id" in payload and payload["research_paper_id"] is not None:
        if not isinstance(payload["research_paper_id"], int) or payload["research_paper_id"] <= 0:
            return None, _error("research_paper_id must be a positive integer or null", 400)
        if db.session.get(ResearchPaper, payload["research_paper_id"]) is None:
            return None, _error("Research paper not found", 404)

    if "author_id" in payload and payload["author_id"] is not None:
        if not isinstance(payload["author_id"], int) or payload["author_id"] <= 0:
            return None, _error("author_id must be a positive integer or null", 400)
        if db.session.get(Author, payload["author_id"]) is None:
            return None, _error("Author not found", 404)

    if "author_order" in payload and payload["author_order"] is not None:
        if not isinstance(payload["author_order"], int):
            return None, _error("author_order must be an integer or null", 400)

    return payload, None


def _serialize_link(link):
    return {
        "research_paper_id": link.research_paper_id,
        "author_id": link.author_id,
        "author_order": link.author_order,
        "research_paper": _serialize_paper(link.research_paper) if link.research_paper else None,
        "author": _serialize_author(link.author) if link.author else None,
    }


def _serialize_paper(paper):
    return {
        "id": paper.id,
        "title": paper.title,
        "department_id": paper.department_id,
    }


def _serialize_author(author):
    return {
        "id": author.id,
        "name": author.name,
        "affiliation": author.affiliation,
        "email": author.email,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code
