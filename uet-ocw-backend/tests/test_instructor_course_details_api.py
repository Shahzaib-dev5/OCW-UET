"""Course detail editing regressions using an isolated database and upload folder."""

from base64 import b64decode
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from flask_jwt_extended import create_access_token
from sqlalchemy import Integer, MetaData

from app import create_app
from app.extensions import db
from app.models.course import Course, CourseStatus
from app.models.department import Department
from app.models.enrollment import ApplicationStatus, CourseTeachingApplication
from app.models.media import MediaFile
from app.models.role import Role
from app.models.user import User


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "course-details-tests-only-secret-key"


class InstructorCourseDetailsApiTests(TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.upload_directory = TemporaryDirectory()
        self.addCleanup(self.upload_directory.cleanup)
        upload_environment = patch.dict("os.environ", {"UPLOAD_FOLDER": self.upload_directory.name})
        upload_environment.start()
        self.addCleanup(upload_environment.stop)
        drive_upload = patch("app.services.file_service.upload_to_google_drive", return_value=(None, None))
        drive_upload.start()
        self.addCleanup(drive_upload.stop)

        with self.app.app_context():
            # SQLite requires INTEGER primary keys for generated IDs. Copy the
            # schema so the application's MySQL model types remain unchanged.
            test_metadata = MetaData()
            for table in db.metadata.sorted_tables:
                copied = table.to_metadata(test_metadata)
                for column in copied.primary_key.columns:
                    column.type = Integer()
            test_metadata.create_all(db.engine)

            db.session.add_all([
                Role(id=1, name="TEACHER"),
                Role(id=2, name="STUDENT"),
                Role(id=3, name="ADMIN"),
                Department(id=1, name="Computer Science"),
            ])
            db.session.add_all([
                self._user(1, "owner"),
                self._user(2, "assigned"),
                self._user(3, "unrelated"),
                self._user(4, "student", role_id=2, instructor_status="NONE"),
                self._user(5, "revoked", instructor_status="REVOKED"),
                self._user(6, "admin", role_id=3, instructor_status="NONE"),
            ])
            db.session.add(Course(
                id=1,
                owner_id=1,
                department_id=1,
                title="Original course",
                slug="original-course",
                description="Original introduction",
                thumbnail="/uploads/original.png",
                syllabus="Original syllabus",
                status=CourseStatus.PUBLISHED,
            ))
            db.session.add_all([
                CourseTeachingApplication(
                    id=1, teacher_id=2, course_id=1, status=ApplicationStatus.APPROVED,
                ),
                CourseTeachingApplication(
                    id=2, teacher_id=3, course_id=1, status=ApplicationStatus.PENDING,
                ),
                CourseTeachingApplication(
                    id=3, teacher_id=5, course_id=1, status=ApplicationStatus.APPROVED,
                ),
            ])
            db.session.commit()
            self.headers = {
                user_id: {"Authorization": f"Bearer {create_access_token(identity=str(user_id))}"}
                for user_id in range(1, 7)
            }

    @staticmethod
    def _user(user_id, username, role_id=1, instructor_status="APPROVED"):
        return User(
            id=user_id, username=username, email=f"{username}@example.test",
            password_hash="unused", role_id=role_id, instructor_status=instructor_status,
        )

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_owner_can_save_course_details_and_submit_changes_for_review(self):
        details = {
            "title": "Updated course name",
            "short_description": "Updated summary",
            "description": "Updated course introduction",
            "syllabus": "Week 1: Foundations\nWeek 2: Practice",
            "learning_outcomes": "Build a complete application",
            "schedule": "Mondays at 10 AM",
            "thumbnail": "/uploads/courses/1/thumbnails/updated.png",
        }
        response = self.client.patch("/api/courses/1", headers=self.headers[1], json=details)
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        saved = self.client.get("/api/courses/1", headers=self.headers[1]).get_json()["data"]
        for field, value in details.items():
            self.assertEqual(saved[field], value)
        self.assertEqual(saved["status"], "DRAFT")
        self.assertEqual(saved["review_status"], "PENDING")
        self.assertEqual(self.client.get("/api/courses/1").status_code, 404)
        self.assertEqual(saved["slug"], "original-course")
        self.assertEqual(saved["owner_id"], 1)

    def test_approved_assigned_instructor_can_edit_details(self):
        response = self.client.patch(
            "/api/courses/1", headers=self.headers[2], json={"title": "Assigned instructor edit"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.get_json()["data"]["title"], "Assigned instructor edit")
        self.assertTrue(response.get_json()["data"]["can_manage"])

    def test_unapproved_and_unrelated_users_cannot_change_details(self):
        for user_id in (None, 3, 4, 5):
            with self.subTest(user_id=user_id):
                response = self.client.patch(
                    "/api/courses/1", headers=self.headers.get(user_id, {}),
                    json={"title": "Unauthorized edit", "thumbnail": "/uploads/unauthorized.png"},
                )
                self.assertEqual(response.status_code, 403)
        with self.app.app_context():
            course = db.session.get(Course, 1)
            self.assertEqual(course.title, "Original course")
            self.assertEqual(course.thumbnail, "/uploads/original.png")

    def test_optional_details_can_be_cleared(self):
        response = self.client.patch(
            "/api/courses/1", headers=self.headers[1],
            json={"description": "", "syllabus": "", "thumbnail": None},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        saved = self.client.get("/api/courses/1", headers=self.headers[1]).get_json()["data"]
        self.assertEqual(saved["description"], "")
        self.assertEqual(saved["syllabus"], "")
        self.assertIsNone(saved["thumbnail"])

    def test_blank_title_is_rejected_without_saving_other_changes(self):
        response = self.client.patch(
            "/api/courses/1", headers=self.headers[1],
            json={"title": "   ", "description": "Should not be saved"},
        )
        self.assertEqual(response.status_code, 400)
        saved = self.client.get("/api/courses/1").get_json()["data"]
        self.assertEqual(saved["title"], "Original course")
        self.assertEqual(saved["description"], "Original introduction")

    def test_editing_draft_does_not_publish_course(self):
        with self.app.app_context():
            db.session.get(Course, 1).status = CourseStatus.DRAFT
            db.session.commit()
        response = self.client.patch(
            "/api/courses/1", headers=self.headers[1], json={"title": "Updated draft"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.get_json()["data"]["status"], "DRAFT")
        self.assertEqual(self.client.get("/api/courses/1").status_code, 404)
        publish = self.client.patch(
            "/api/courses/1", headers=self.headers[1], json={"status": "PUBLISHED"},
        )
        self.assertEqual(publish.status_code, 403)

    def test_instructor_can_upload_and_replace_course_image(self):
        image_bytes = b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jCqkAAAAASUVORK5CYII="
        )
        upload = self.client.post(
            "/api/uploads", headers=self.headers[1], content_type="multipart/form-data",
            data={
                "file": (BytesIO(image_bytes), "updated-course.png", "image/png"),
                "folder": "courses/1/thumbnails",
            },
        )
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))
        image_url = upload.get_json()["local_url"]
        self.assertTrue(image_url.startswith("/uploads/courses/1/thumbnails/"))
        response = self.client.patch(
            "/api/courses/1", headers=self.headers[1], json={"thumbnail": image_url},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        saved_course = self.client.get("/api/courses/1", headers=self.headers[1]).get_json()["data"]
        self.assertEqual(saved_course["thumbnail"], image_url)
        self.assertEqual(self.client.get(image_url).status_code, 403)
        image_response = self.client.get(image_url, headers=self.headers[1])
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response.data, image_bytes)
        image_response.close()
        with self.app.app_context():
            media = db.session.get(MediaFile, upload.get_json()["media_id"])
            self.assertEqual(media.uploaded_by, 1)

