import mimetypes
import os
import posixpath
import re
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request, send_from_directory
from sqlalchemy import func, or_, select

from config import Config
from app.extensions import db, migrate, cors, jwt


def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    jwt.init_app(app)

    @app.before_request
    def limit_moderator_writes():
        # Enforce the review-only role across all present and future API writes.
        if request.method in {"GET", "HEAD", "OPTIONS"} or not request.path.startswith("/api/"):
            return None
        allowed = {
            "moderation.approve_course", "moderation.reject_course",
            "auth.login", "auth.google_auth", "auth.verify_email_otp", "auth.resend_email_otp",
            "auth.forgot_password", "auth.reset_password", "auth.logout",
        }
        if request.endpoint in allowed:
            return None
        from app.services.authz import MODERATOR, role_name
        if role_name() == MODERATOR:
            return jsonify(status="error", message="Moderators may only view content and approve or reject courses"), 403
        return None

    @app.route("/openapi.json")
    def openapi_json():
        return jsonify(_build_openapi_spec(app))

    @app.route("/apidocs")
    def apidocs():
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8" />
                <title>UET OCW API Docs</title>
                <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.0.0/swagger-ui.css" />
                <style>
                    html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
                    *, *:before, *:after { box-sizing: inherit; }
                    body { margin:0; background: #fafafa; }
                    #swagger-ui { max-width: 1200px; margin: 0 auto; }
                </style>
            </head>
            <body>
                <div id="swagger-ui"></div>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.0.0/swagger-ui-bundle.js"></script>
                <script>
                    SwaggerUIBundle({
                        url: '/openapi.json',
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
                        layout: 'BaseLayout'
                    });
                </script>
            </body>
            </html>
        """)

    @app.route("/api/health")
    def health():
        return {
            "status": "success",
            "message": "UET Open Courseware API is running"
        }

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        if not _can_serve_upload(filename):
            return jsonify({"status": "error", "message": "Authentication or approved enrollment is required for this file"}), 403
        upload_root = _resolve_upload_root()
        guessed_mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        response = send_from_directory(
            upload_root,
            filename,
            mimetype=guessed_mimetype,
            as_attachment=False,
            download_name=Path(filename).name,
        )
        safe_filename = Path(filename).name.replace('"', "")
        response.headers["Content-Disposition"] = f'inline; filename="{safe_filename}"'
        return response

    @app.route("/upload-test")
    def upload_test_page():
        return render_template_string('''
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <title>Upload Test</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 700px; margin: 50px auto; padding: 20px; }
                    form { border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
                    input, button { display: block; width: 100%; margin-top: 12px; padding: 10px; box-sizing: border-box; }
                    #result { margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px; white-space: pre-wrap; }
                </style>
            </head>
            <body>
                <h2>Upload Test</h2>
                <form id="uploadForm" enctype="multipart/form-data">
                    <label>File</label>
                    <input type="file" name="file" id="file" required>
                    <label>Folder</label>
                    <input type="text" name="folder" id="folder" value="courses/1/resources" placeholder="courses/1/resources">
                    <button type="submit">Upload</button>
                </form>
                <div id="result">Waiting for upload...</div>

                <script>
                    const form = document.getElementById('uploadForm');
                    const result = document.getElementById('result');

                    form.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        const formData = new FormData(form);

                        result.textContent = 'Uploading...';
                        try {
                            const res = await fetch('/api/uploads', {
                                method: 'POST',
                                body: formData
                            });
                            const data = await res.json();
                            result.textContent = JSON.stringify(data, null, 2);
                        } catch (err) {
                            result.textContent = 'Upload failed: ' + err.message;
                        }
                    });
                </script>
            </body>
            </html>
        ''')

    # Import models
    from app import models

    # Import routes
    from app.routes.admin_dashboard import admin_dashboard_bp
    from app.routes.teacher_dashboard import teacher_dashboard_bp
    from app.routes.auth import auth_bp
    from app.routes.roles import roles_bp
    from app.routes.users import users_bp
    from app.routes.faculties import faculties_bp
    from app.routes.departments import departments_bp
    from app.routes.courses import courses_bp
    from app.routes.course_resources import course_resources_bp
    from app.routes.lectures import lectures_bp
    from app.routes.authors import authors_bp
    from app.routes.research_authors import research_authors_bp
    from app.routes.internships import internships_bp, skills_development_bp
    from app.routes.internship_resources import internship_resources_bp, skills_development_resources_bp
    from app.routes.invited_talks import invited_talks_bp
    from app.routes.research import research_bp
    from app.routes.menu import menu_bp
    from app.routes.media import media_bp
    from app.routes.uploads import uploads_bp
    from app.routes.course_teaching_applications import course_teaching_applications_bp
    from app.routes.course_enrollments import course_enrollments_bp
    from app.routes.instructor_applications import instructor_applications_bp
    from app.routes.moderation import moderation_bp
    from app.routes.moderator_dashboard import moderator_dashboard_bp

    # Register routes
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(teacher_dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(faculties_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(course_resources_bp)
    app.register_blueprint(lectures_bp)
    app.register_blueprint(authors_bp)
    app.register_blueprint(research_authors_bp)
    app.register_blueprint(internships_bp)
    app.register_blueprint(skills_development_bp)
    app.register_blueprint(internship_resources_bp)
    app.register_blueprint(skills_development_resources_bp)
    app.register_blueprint(invited_talks_bp)
    app.register_blueprint(research_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(course_teaching_applications_bp)
    app.register_blueprint(course_enrollments_bp)
    app.register_blueprint(instructor_applications_bp)
    app.register_blueprint(moderation_bp)
    app.register_blueprint(moderator_dashboard_bp)

    return app


def _resolve_upload_root():
    """Resolve relative upload folders from the backend project root.

    Flask resolves relative ``send_from_directory`` paths from the application
    package, while upload writes normally resolve them from the process working
    directory. Resolving once here keeps reads and writes pointed at the same
    directory in local development and production services.
    """
    backend_root = Path(__file__).resolve().parents[1]
    configured = Path(os.getenv("UPLOAD_FOLDER", "uploads")).expanduser()
    if not configured.is_absolute():
        configured = backend_root / configured
    return configured.resolve()


def _can_serve_upload(filename):
    # Match the path that send_from_directory will resolve, including aliases
    # containing dot segments and case variants on Windows installations.
    normalized = posixpath.normpath(f"/uploads/{filename}".replace("\\", "/")).lower()
    with db.session.no_autoflush:
        from app.models.course import Course
        from app.models.internship import Internship
        from app.models.internship_resource import InternshipResource
        from app.models.lecture import Lecture
        from app.models.resource import CourseResource
        from app.services.authz import can_view_book_learning, can_view_course_learning, can_view_course_record, can_view_skill_learning

        course = db.session.scalar(select(Course).where(func.lower(Course.thumbnail) == normalized).limit(1))
        if course is not None:
            return can_view_course_record(course)
        skill = db.session.scalar(select(Internship).where(func.lower(Internship.thumbnail) == normalized).limit(1))
        if skill is not None:
            return True

        lecture = db.session.scalar(
            select(Lecture).where(
                or_(
                    func.lower(Lecture.video_url) == normalized,
                    func.lower(Lecture.presentation_url) == normalized,
                    func.lower(Lecture.notes_url) == normalized,
                )
            ).limit(1)
        )
        if lecture is not None:
            return can_view_course_learning(lecture.course_id)

        course_resource = db.session.scalar(
            select(CourseResource).where(or_(func.lower(CourseResource.file_url) == normalized, func.lower(CourseResource.external_url) == normalized,
                                            func.lower(CourseResource.thumbnail) == normalized)).limit(1)
        )
        if course_resource is not None:
            if course_resource.resource_type and course_resource.resource_type.value == "BOOK":
                return can_view_book_learning(course_resource.id)
            return can_view_course_learning(course_resource.course_id)

        skill_resource = db.session.scalar(
            select(InternshipResource).where(func.lower(InternshipResource.file_url) == normalized).limit(1)
        )
        if skill_resource is not None:
            return can_view_skill_learning(skill_resource.internship_id)

        # Uploads may exist before a lecture/resource row has been attached.
        course_path = re.match(r"^/uploads/courses/(\d+)(?:/|$)", normalized)
        if course_path:
            return can_view_course_learning(int(course_path.group(1)))

    return True


def _build_openapi_spec(app):
    paths = {}
    tags = [
        {"name": "Auth", "description": "Authentication and health endpoints"},
        {"name": "Roles", "description": "Role and permission APIs"},
        {"name": "Users", "description": "User and role assignment APIs"},
        {"name": "Course Teaching Applications", "description": "Teacher course application and approval APIs"},
        {"name": "Course Enrollments", "description": "Student course application and approval APIs"},
        {"name": "Faculties", "description": "Faculty management APIs"},
        {"name": "Departments", "description": "Department management APIs"},
        {"name": "Courses", "description": "Course management APIs"},
        {"name": "Course Moderation", "description": "ADMIN/MODERATOR review queue, preview and publication decisions"},
        {"name": "Course Resources", "description": "Course resource upload and management APIs"},
        {"name": "Lectures", "description": "Lecture management APIs"},
        {"name": "Authors", "description": "Research author management APIs"},
        {"name": "Research Paper Authors", "description": "Research paper to author linking APIs"},
        {"name": "Skills Development", "description": "Skills development program management APIs"},
        {"name": "Skills Development Resources", "description": "Skills development resource upload and management APIs"},
        {"name": "Invited Talks", "description": "Department-based invited talk APIs"},
        {"name": "Research Papers", "description": "Research paper APIs"},
        {"name": "Menu", "description": "Menu management APIs"},
        {"name": "Media", "description": "Media file upload and management APIs"},
    ]

    for rule in sorted(app.url_map.iter_rules(), key=lambda item: item.rule):
        endpoint_name = rule.endpoint
        if endpoint_name in {
            "static",
            "openapi_json",
            "apidocs",
            "health",
            "uploaded_file",
            "admin_dashboard.admin_index",
            "admin_dashboard.admin_login",
            "admin_dashboard.admin_dashboard",
            "teacher_dashboard.teacher_index",
            "teacher_dashboard.teacher_login",
            "teacher_dashboard.teacher_dashboard",
            "moderator_dashboard.moderator_index",
            "moderator_dashboard.moderator_dashboard",
        }:
            continue

        methods = [m.lower() for m in rule.methods if m not in {"HEAD", "OPTIONS"}]
        if not methods:
            continue

        path = _convert_flask_path_to_openapi(rule.rule)
        tag = _tag_for_path(path)

        paths.setdefault(path, {})
        for method in methods:
            operation = {
                "tags": [tag],
                "summary": f"{tag} {method.upper()}",
                "responses": {
                    "200": {"description": "Successful response"},
                    "201": {"description": "Created"},
                    "400": {"description": "Bad request"},
                    "401": {"description": "Authentication required"},
                    "403": {"description": "Insufficient permissions"},
                    "404": {"description": "Not found"},
                    "409": {"description": "Conflict"},
                    "500": {"description": "Server error"}
                }
            }

            if method in {"get", "delete"}:
                operation["parameters"] = _build_path_parameters(path)
            if method in {"post", "put", "patch"}:
                operation["parameters"] = _build_path_parameters(path)
                request_content = {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": _schema_for_route(path),
                            "additionalProperties": True,
                        }
                    }
                }
                if (
                    path == "/api/uploads"
                    or path.startswith("/api/internship-resources")
                    or path.startswith("/api/skills-development-resources")
                    or path.startswith("/api/invited-talks")
                    or path.startswith("/api/research-papers")
                ):
                    request_content["multipart/form-data"] = {
                        "schema": {
                            "type": "object",
                            "properties": _schema_for_route(path),
                            "additionalProperties": True,
                        }
                    }
                operation["requestBody"] = {
                    "required": True,
                    "content": request_content,
                }

            if path.startswith("/api/moderation/"):
                operation["security"] = [{"bearerAuth": []}]
                operation["description"] = "Available only to ADMIN and MODERATOR. Moderators cannot create, edit, delete or upload content."
                if path == "/api/moderation/courses" and method == "get":
                    operation["parameters"] += [
                        {"name": name, "in": "query", "schema": {"type": "integer", "minimum": 1}}
                        for name in ("faculty_id", "department_id", "instructor_id", "page", "per_page")
                    ] + [
                        {"name": "status", "in": "query", "schema": {"type": "string", "enum": ["PENDING", "APPROVED", "REJECTED", "ALL"], "default": "PENDING"}},
                        {"name": "q", "in": "query", "schema": {"type": "string", "maxLength": 200}},
                    ]
                if method == "post":
                    schema = operation["requestBody"]["content"]["application/json"]["schema"]
                    schema["additionalProperties"] = False
                    schema["required"] = ["review_version"] + (["reason"] if path.endswith("/reject") else [])
                    operation["responses"]["409"]["description"] = "Course content or review changed; reload the preview before deciding"
            paths[path][method] = operation

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "UET OCW API",
            "version": "1.0.0",
            "description": "OpenAPI documentation for all project APIs"
        },
        "tags": tags,
        "components": {"securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}}},
        "x-tagGroups": [
            {"name": "Core", "tags": ["Auth", "Roles", "Users", "Menu", "Media"]},
            {"name": "Academic", "tags": ["Faculties", "Departments", "Courses", "Course Moderation", "Course Resources", "Lectures", "Authors", "Research Paper Authors", "Skills Development", "Skills Development Resources", "Invited Talks", "Research Papers", "Course Teaching Applications", "Course Enrollments"]},
        ],
        "paths": paths,
    }


def _build_path_parameters(path):
    params = []
    for segment in path.split('/'):
        if segment.startswith('{') and segment.endswith('}'):
            name = segment.strip('{}')
            params.append({
                "name": name,
                "in": "path",
                "required": True,
                "schema": {"type": "integer"},
                "description": f"{name} identifier"
            })
    return params


def _schema_for_route(path):
    if path.startswith('/api/moderation/'):
        return {
            "review_version": {"type": "integer", "minimum": 0, "example": 0, "description": "Version returned by the course preview; stale versions receive 409"},
            "reason": {"type": "string", "maxLength": 2000, "example": "Please replace the unreadable lecture notes", "description": "Required when rejecting a course"},
        }
    if '/api/faculties' in path:
        return {
            "name": {"type": "string", "example": "Computer Science"},
            "short_name": {"type": "string", "example": "CS"},
            "description": {"type": "string", "example": "Faculty overview"},
            "logo": {"type": "string", "nullable": True, "example": "/uploads/logo.png"},
            "website_url": {"type": "string", "nullable": True, "example": "https://example.edu"},
            "display_order": {"type": "integer", "example": 1},
            "is_active": {"type": "boolean", "example": True},
        }
    if '/api/departments' in path:
        return {
            "faculty_id": {"type": "integer", "example": 1},
            "name": {"type": "string", "example": "Software Engineering"},
            "short_name": {"type": "string", "example": "SE"},
            "department_type": {"type": "string", "example": "academic"},
            "description": {"type": "string", "example": "Department details"},
            "logo": {"type": "string", "nullable": True, "example": "/uploads/department.png"},
            "website_url": {"type": "string", "nullable": True, "example": "https://example.edu/department"},
            "display_order": {"type": "integer", "example": 1},
            "is_active": {"type": "boolean", "example": True},
        }
    if '/api/courses' in path:
        return {
            "department_id": {"type": "integer", "example": 1},
            "course_code": {"type": "string", "example": "CS101"},
            "title": {"type": "string", "example": "Intro to Programming"},
            "slug": {"type": "string", "example": "intro-to-programming"},
            "short_description": {"type": "string", "example": "Basic programming concepts"},
            "description": {"type": "string", "example": "Detailed course syllabus."},
            "category": {"type": "string", "example": "Humanities"},
            "credit_hours": {"type": "integer", "example": 3},
            "duration": {"type": "string", "example": "32 lectures"},
            "course_type": {"type": "string", "example": "Hybrid"},
            "syllabus": {"type": "string", "example": "Week by week syllabus details."},
            "instructor_name": {"type": "string", "example": "Dr. Ali"},
            "instructor_email": {"type": "string", "example": "ali@example.edu"},
            "level": {"type": "string", "example": "undergraduate"},
            "semester": {"type": "string", "example": "Spring 2026"},
            "academic_year": {"type": "string", "example": "2025-2026"},
            "thumbnail": {"type": "string", "nullable": True, "example": "/uploads/course.jpg"},
            "status": {"type": "string", "example": "published"},
            "display_order": {"type": "integer", "example": 1},
        }
    if '/api/internships' in path or ('/api/skills-development' in path and '/api/skills-development-resources' not in path):
        return {
            "department_id": {"type": "integer", "example": 1},
            "title": {"type": "string", "example": "AI Skills Bootcamp"},
            "slug": {"type": "string", "example": "ai-skills-bootcamp"},
            "description": {"type": "string", "example": "Skills development program details"},
            "category": {"type": "string", "example": "technical training"},
            "duration": {"type": "string", "example": "8 weeks"},
            "eligibility": {"type": "string", "example": "Final-year students"},
            "application_url": {"type": "string", "example": "https://example.edu/apply"},
            "thumbnail": {"type": "string", "nullable": True, "example": "/uploads/skills-development/thumb.jpg"},
            "start_date": {"type": "string", "format": "date", "example": "2026-06-01"},
            "end_date": {"type": "string", "format": "date", "example": "2026-07-31"},
            "status": {"type": "string", "example": "open"},
            "display_order": {"type": "integer", "example": 1},
        }
    if '/api/lectures' in path:
        return {
            "course_id": {"type": "integer", "example": 1},
            "lecture_number": {"type": "integer", "example": 1},
            "title": {"type": "string", "example": "Introduction to Python"},
            "description": {"type": "string", "example": "Overview of variables and loops"},
            "duration_minutes": {"type": "integer", "example": 45},
            "video_url": {"type": "string", "nullable": True, "example": "/uploads/video.mp4"},
            "presentation_url": {"type": "string", "nullable": True, "example": "/uploads/slides.pdf"},
            "notes_url": {"type": "string", "nullable": True, "example": "/uploads/notes.md"},
            "is_published": {"type": "boolean", "example": True},
            "display_order": {"type": "integer", "example": 1},
        }
    if '/api/research-authors' in path:
        return {
            "research_paper_id": {"type": "integer", "example": 1},
            "author_id": {"type": "integer", "example": 2},
            "author_order": {"type": "integer", "example": 1},
        }
    if '/api/research' in path:
        return {
            "department_id": {"type": "integer", "example": 1},
            "title": {"type": "string", "example": "AI for Smart Education"},
            "abstract": {"type": "string", "example": "This paper explores AI-driven learning systems."},
            "authors": {"type": "string", "example": "Ali Khan, Sara Ahmed"},
            "publication_type": {"type": "string", "example": "journal"},
            "publication_date": {"type": "string", "format": "date", "example": "2026-09-16"},
            "publication_title": {"type": "string", "example": "Journal of Computing"},
            "journal_name": {"type": "string", "example": "Journal of Computing"},
            "conference_name": {"type": "string", "example": "ICET"},
            "publication_year": {"type": "integer", "example": 2026},
            "doi": {"type": "string", "example": "10.1000/example"},
            "keywords": {"type": "string", "example": "AI, Education, Data"},
            "paper_url": {"type": "string", "example": "https://example.edu/paper"},
            "pdf_file": {"type": "string", "format": "binary"},
            "pdf_url": {"type": "string", "example": "/uploads/paper.pdf"},
            "status": {"type": "string", "example": "PUBLISHED"},
            "display_order": {"type": "integer", "example": 1},
        }
    if '/api/course-resources' in path:
        return {
            "course_id": {"type": "integer", "example": 1},
            "title": {"type": "string", "example": "Week 1 Lecture PDF"},
            "resource_type": {"type": "string", "example": "pdf"},
            "description": {"type": "string", "example": "Lecture material"},
            "file_url": {"type": "string", "nullable": True, "example": "/uploads/course.pdf"},
            "external_url": {"type": "string", "nullable": True, "example": "https://example.com/resource"},
            "file_size": {"type": "integer", "nullable": True, "example": 120000},
            "mime_type": {"type": "string", "nullable": True, "example": "application/pdf"},
            "lecture_number": {"type": "integer", "nullable": True, "example": 1},
            "display_order": {"type": "integer", "example": 1},
            "is_active": {"type": "boolean", "example": True},
        }
    if '/api/internship-resources' in path or '/api/skills-development-resources' in path:
        return {
            "internship_id": {"type": "integer", "example": 1},
            "title": {"type": "string", "example": "Guidelines PDF"},
            "resource_type": {"type": "string", "example": "PDF"},
            "description": {"type": "string", "nullable": True, "example": "Skills development program guidelines"},
            "file": {"type": "string", "format": "binary"},
            "file_url": {"type": "string", "nullable": True, "example": "/uploads/skills-development.pdf"},
            "external_url": {"type": "string", "nullable": True, "example": "https://example.com/guidelines"},
            "file_size": {"type": "integer", "nullable": True, "example": 120000},
            "mime_type": {"type": "string", "nullable": True, "example": "application/pdf"},
            "display_order": {"type": "integer", "example": 1},
            "is_active": {"type": "boolean", "example": True},
        }
    if '/api/invited-talks' in path:
        return {
            "department_id": {"type": "integer", "example": 1},
            "talk_title": {"type": "string", "example": "AI for Sustainable Engineering"},
            "event_title": {"type": "string", "example": "UET Research Seminar Series"},
            "presenter": {"type": "string", "example": "Dr. Sara Ahmed"},
            "talk_date": {"type": "string", "format": "date", "example": "2026-10-01"},
            "video_url": {"type": "string", "nullable": True, "example": "https://example.com/talk-video"},
            "upload_file": {"type": "string", "format": "binary"},
            "upload_url": {"type": "string", "nullable": True, "example": "/uploads/invited-talks/slides.pdf"},
            "publication": {"type": "string", "nullable": True, "example": "Published in UET Seminar Proceedings"},
            "status": {"type": "string", "example": "PUBLISHED"},
            "display_order": {"type": "integer", "example": 1},
        }
    if '/api/uploads' in path:
        return {
            "file": {"type": "string", "format": "binary"},
            "folder": {"type": "string", "example": "courses"},
        }
    if '/api/roles' in path:
        return {
            "name": {"type": "string", "example": "TEACHER"},
            "description": {"type": "string", "nullable": True, "example": "Can manage approved course resources"},
        }
    if '/api/users' in path:
        return {
            "role": {"type": "string", "example": "TEACHER"},
            "role_id": {"type": "integer", "nullable": True, "example": 2},
            "username": {"type": "string", "example": "teacher1"},
            "email": {"type": "string", "example": "teacher1@example.edu"},
            "password": {"type": "string", "nullable": True, "example": "secret123"},
            "generate_password": {"type": "boolean", "example": True},
            "full_name": {"type": "string", "nullable": True, "example": "Teacher One"},
        }
    if '/api/course-teaching-applications' in path:
        return {
            "course_id": {"type": "integer", "example": 1},
            "message": {"type": "string", "nullable": True, "example": "I want to teach this course"},
        }
    if '/api/course-enrollments' in path:
        return {
            "course_id": {"type": "integer", "example": 1},
            "message": {"type": "string", "nullable": True, "example": "I want to enroll in this course"},
        }
    if '/api/auth' in path:
        return {
            "username": {"type": "string", "example": "admin"},
            "email": {"type": "string", "example": "admin@example.edu"},
            "password": {"type": "string", "example": "secret"},
            "role": {"type": "string", "example": "ADMIN"},
            "full_name": {"type": "string", "nullable": True, "example": "System Admin"},
        }
    if '/api/menu' in path:
        return {
            "parent_id": {"type": "integer", "nullable": True, "example": None},
            "title": {"type": "string", "example": "Home"},
            "slug": {"type": "string", "nullable": True, "example": "home"},
            "url": {"type": "string", "nullable": True, "example": "/"},
            "menu_location": {"type": "string", "example": "HEADER"},
            "icon": {"type": "string", "nullable": True, "example": "home"},
            "display_order": {"type": "integer", "example": 1},
            "is_active": {"type": "boolean", "example": True},
        }
    if '/api/media' in path:
        return {
            "original_name": {"type": "string", "example": "document.pdf"},
            "stored_name": {"type": "string", "nullable": True, "example": "doc_12345.pdf"},
            "file_path": {"type": "string", "nullable": True, "example": "/uploads/courses/doc_12345.pdf"},
            "file_url": {"type": "string", "nullable": True, "example": "/uploads/courses/doc_12345.pdf"},
            "mime_type": {"type": "string", "nullable": True, "example": "application/pdf"},
            "file_size": {"type": "integer", "nullable": True, "example": 120000},
            "uploaded_by": {"type": "integer", "nullable": True, "example": 1},
        }
    return {
        "data": {"type": "object", "example": {}}
    }


def _tag_for_path(path):
    if "/api/moderation/" in path:
        return "Course Moderation"
    if "/api/auth" in path and "/api/authors" not in path:
        return "Auth"
    if "/api/roles" in path:
        return "Roles"
    if "/api/users" in path:
        return "Users"
    if "/api/course-teaching-applications" in path:
        return "Course Teaching Applications"
    if "/api/course-enrollments" in path:
        return "Course Enrollments"
    if "/api/faculties" in path:
        return "Faculties"
    if "/api/departments" in path:
        return "Departments"
    if "/api/courses" in path:
        return "Courses"
    if "/api/course-resources" in path:
        return "Course Resources"
    if "/api/lectures" in path:
        return "Lectures"
    if "/api/authors" in path:
        return "Authors"
    if "/api/research-authors" in path or "/api/research-paper-authors" in path:
        return "Research Paper Authors"
    if "/api/internship-resources" in path or "/api/skills-development-resources" in path:
        return "Skills Development Resources"
    if "/api/internships" in path or "/api/skills-development" in path:
        return "Skills Development"
    if "/api/invited-talks" in path:
        return "Invited Talks"
    if "/api/research" in path or "/api/research-papers" in path:
        return "Research Papers"
    if "/api/menu" in path:
        return "Menu"
    if "/api/media" in path:
        return "Media"
    if "/api/uploads" in path:
        return "Media"
    return "General"


def _convert_flask_path_to_openapi(rule_path):
    return rule_path.replace("<int:", "{").replace(">", "}")
