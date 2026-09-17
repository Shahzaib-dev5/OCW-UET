from io import BytesIO

from flask_jwt_extended import create_access_token

from app import create_app
from app.extensions import db
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.internship import Internship, InternshipStatus
from app.models.role import Role
from app.models.user import User


class TestConfig:
    SECRET_KEY = "test"
    JWT_SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True


def test_internship_resource_upload_crud(tmp_path):
    app = create_app(TestConfig)
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    with app.app_context():
        db.create_all()
        admin_role = Role(id=1, name="ADMIN", description="Admin")
        admin = User(
            id=1,
            role=admin_role,
            username="admin",
            email="admin@example.edu",
            password_hash="unused",
        )
        faculty = Faculty(id=1, name="Engineering")
        department = Department(id=1, faculty=faculty, name="Software Engineering")
        internship = Internship(
            id=1,
            department=department,
            title="Summer Internship",
            slug="summer-internship",
            status=InternshipStatus.OPEN,
        )
        db.session.add_all([admin_role, admin, faculty, department, internship])
        db.session.commit()
        token = create_access_token(identity=str(admin.id))

    client = app.test_client()
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/internship-resources",
        data={
            "internship_id": "1",
            "title": "Guidelines",
            "resource_type": "PDF",
            "description": "Application notes",
            "display_order": "2",
            "file": (BytesIO(b"hello internship"), "guidelines.txt"),
        },
        headers=headers,
        content_type="multipart/form-data",
    )
    assert create_response.status_code == 201, create_response.get_data(as_text=True)
    created = create_response.get_json()["data"]
    assert created["file_url"].startswith("/uploads/internships/1/resources/")
    assert created["file_size"] == len(b"hello internship")
    assert created["mime_type"] == "text/plain"

    resource_id = created["id"]
    list_response = client.get("/api/internship-resources/internship/1")
    assert list_response.status_code == 200
    assert list_response.get_json()["data"][0]["id"] == resource_id

    update_response = client.patch(
        f"/api/internship-resources/{resource_id}",
        json={"title": "Updated Guidelines", "is_active": False},
        headers=headers,
    )
    assert update_response.status_code == 200, update_response.get_data(as_text=True)
    updated = update_response.get_json()["data"]
    assert updated["title"] == "Updated Guidelines"
    assert updated["is_active"] is False

    delete_response = client.delete(f"/api/internship-resources/{resource_id}", headers=headers)
    assert delete_response.status_code == 200, delete_response.get_data(as_text=True)

    show_response = client.get(f"/api/internship-resources/{resource_id}")
    assert show_response.status_code == 404
