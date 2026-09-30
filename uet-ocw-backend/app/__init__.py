import mimetypes
import os
from pathlib import Path

from flask import Flask, jsonify, render_template_string, send_from_directory

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
        upload_root = os.getenv("UPLOAD_FOLDER", str(Path(__file__).resolve().parents[1] / "uploads"))
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
    from app.routes.internships import internships_bp
    from app.routes.internship_resources import internship_resources_bp
    from app.routes.research import research_bp
    from app.routes.menu import menu_bp
    from app.routes.media import media_bp
    from app.routes.uploads import uploads_bp
    from app.routes.course_teaching_applications import course_teaching_applications_bp
    from app.routes.course_enrollments import course_enrollments_bp

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
    app.register_blueprint(internship_resources_bp)
    app.register_blueprint(research_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(course_teaching_applications_bp)
    app.register_blueprint(course_enrollments_bp)

    return app


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
        {"name": "Course Resources", "description": "Course resource upload and management APIs"},
        {"name": "Lectures", "description": "Lecture management APIs"},
        {"name": "Authors", "description": "Research author management APIs"},
        {"name": "Research Paper Authors", "description": "Research paper to author linking APIs"},
        {"name": "Internships", "description": "Internship management APIs"},
        {"name": "Internship Resources", "description": "Internship resource upload and management APIs"},
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

            paths[path][method] = operation

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "UET OCW API",
            "version": "1.0.0",
            "description": "OpenAPI documentation for all project APIs"
        },
        "tags": tags,
        "x-tagGroups": [
            {"name": "Core", "tags": ["Auth", "Roles", "Users", "Menu", "Media"]},
            {"name": "Academic", "tags": ["Faculties", "Departments", "Courses", "Course Resources", "Lectures", "Authors", "Research Paper Authors", "Internships", "Internship Resources", "Research Papers", "Course Teaching Applications", "Course Enrollments"]},
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
    if '/api/internships' in path:
        return {
            "department_id": {"type": "integer", "example": 1},
            "title": {"type": "string", "example": "Summer Internship"},
            "slug": {"type": "string", "example": "summer-internship"},
            "description": {"type": "string", "example": "Internship details"},
            "category": {"type": "string", "example": "industry"},
            "duration": {"type": "string", "example": "8 weeks"},
            "eligibility": {"type": "string", "example": "Final-year students"},
            "application_url": {"type": "string", "example": "https://example.edu/apply"},
            "thumbnail": {"type": "string", "nullable": True, "example": "/uploads/internships/thumb.jpg"},
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
    if '/api/internship-resources' in path:
        return {
            "internship_id": {"type": "integer", "example": 1},
            "title": {"type": "string", "example": "Guidelines PDF"},
            "resource_type": {"type": "string", "example": "PDF"},
            "description": {"type": "string", "nullable": True, "example": "Internship application guidelines"},
            "file": {"type": "string", "format": "binary"},
            "file_url": {"type": "string", "nullable": True, "example": "/uploads/internship.pdf"},
            "external_url": {"type": "string", "nullable": True, "example": "https://example.com/guidelines"},
            "file_size": {"type": "integer", "nullable": True, "example": 120000},
            "mime_type": {"type": "string", "nullable": True, "example": "application/pdf"},
            "display_order": {"type": "integer", "example": 1},
            "is_active": {"type": "boolean", "example": True},
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
    if "/api/internship-resources" in path:
        return "Internship Resources"
    if "/api/internships" in path:
        return "Internships"
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
