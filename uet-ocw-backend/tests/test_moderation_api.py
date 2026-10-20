"""Moderator permissions and course review workflow, without a live database."""

from io import BytesIO
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from flask_jwt_extended import create_access_token
from sqlalchemy import Integer, MetaData, select

from app import create_app
from app.extensions import db
from app.models.course import AccessLevel, Course, CourseStatus
from app.models.department import Department
from app.models.enrollment import ApplicationStatus, CourseEnrollment, CourseTeachingApplication
from app.models.faculty import Faculty
from app.models.lecture import Lecture
from app.models.resource import CourseResource, CourseResourceType
from app.models.role import Role
from app.models.user import User


class ModerationTestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "moderation-tests-only-secret-key-123"


class ModerationApiTests(TestCase):
    def setUp(self):
        self.app = create_app(ModerationTestConfig)
        self.client = self.app.test_client()
        uploads = TemporaryDirectory()
        self.addCleanup(uploads.cleanup)
        self.upload_root = Path(uploads.name)
        for replacement in (
            patch.dict("os.environ", {"UPLOAD_FOLDER": uploads.name}),
            patch("app.services.file_service.upload_to_google_drive", return_value=(None, None)),
            patch("app.routes.auth._send_email_otp", return_value=True),
        ):
            replacement.start()
            self.addCleanup(replacement.stop)

        with self.app.app_context():
            # Preserve MySQL model types while allowing generated IDs in SQLite.
            test_metadata = MetaData()
            for table in db.metadata.sorted_tables:
                copied = table.to_metadata(test_metadata)
                for column in copied.primary_key.columns:
                    column.type = Integer()
            test_metadata.create_all(db.engine)
            db.session.add_all([
                Role(id=1, name="ADMIN"), Role(id=2, name="MODERATOR"),
                Role(id=3, name="TEACHER"), Role(id=4, name="STUDENT"),
                Faculty(id=1, name="Science"), Faculty(id=2, name="Engineering"),
                Department(id=1, name="Computing", faculty_id=1),
                Department(id=2, name="Electrical", faculty_id=2),
                Department(id=3, name="Mathematics", faculty_id=1),
            ])
            for user_id, role_id, name, status in (
                (1, 1, "admin", "NONE"), (2, 2, "moderator", "APPROVED"),
                (3, 3, "alice", "APPROVED"), (4, 3, "bob", "APPROVED"),
                (5, 4, "student", "NONE"), (6, 2, "reviewer", "NONE"),
            ):
                db.session.add(User(
                    id=user_id, role_id=role_id, username=name, full_name=name.title(),
                    email=f"{name}@example.test", password_hash="unused",
                    instructor_status=status, email_verified=True,
                ))
            course_data = (
                (1, 1, 3, "Pending algorithms", "PENDING"),
                (2, 1, 3, "Approved programming", "APPROVED"),
                (3, 2, 4, "Rejected circuits", "REJECTED"),
                (4, 2, 2, "Former instructor course", "PENDING"),
                (5, 3, 4, "Pending mathematics", "PENDING"),
            )
            for course_id, department_id, owner_id, title, review_status in course_data:
                db.session.add(Course(
                    id=course_id, department_id=department_id, owner_id=owner_id,
                    title=title, slug=f"course-{course_id}", description=f"About {title}",
                    instructor_name="Alice" if owner_id == 3 else "Bob",
                    status=CourseStatus.PUBLISHED if review_status == "APPROVED" else CourseStatus.DRAFT,
                    review_status=review_status, review_version=0,
                    access_level=AccessLevel.RESTRICTED if course_id == 1 else AccessLevel.PUBLIC,
                    login_required=course_id == 1,
                ))
                lecture_path = f"courses/{course_id}/lecture.txt"
                resource_path = f"courses/{course_id}/resource.pdf"
                for relative_path in (lecture_path, resource_path):
                    file_path = self.upload_root / relative_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(f"Course {course_id} review material".encode())
                db.session.add(Lecture(
                    id=course_id, course_id=course_id, lecture_number=1,
                    title=f"Lecture {course_id}", notes_url=f"/uploads/{lecture_path}",
                    is_published=course_id == 2,
                ))
                db.session.add(CourseResource(
                    id=course_id, course_id=course_id, owner_id=owner_id,
                    title=f"Resource {course_id}", resource_type=CourseResourceType.PDF,
                    file_url=f"/uploads/{resource_path}", is_active=course_id == 2,
                ))
            db.session.add(CourseResource(
                id=6, owner_id=2, title="Moderator's former book",
                resource_type=CourseResourceType.BOOK, access_level=AccessLevel.RESTRICTED,
            ))
            db.session.add(CourseTeachingApplication(
                id=1, teacher_id=2, course_id=1, status=ApplicationStatus.APPROVED,
            ))
            db.session.add(CourseTeachingApplication(
                id=2, teacher_id=4, course_id=2, status=ApplicationStatus.APPROVED,
            ))
            db.session.add_all([
                CourseEnrollment(id=1, student_id=5, course_id=1, status=ApplicationStatus.APPROVED),
                CourseEnrollment(id=2, student_id=5, course_id=3, status=ApplicationStatus.APPROVED),
            ])
            db.session.commit()
            self.headers = {
                user_id: {"Authorization": f"Bearer {create_access_token(identity=str(user_id))}"}
                for user_id in range(1, 7)
            }

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def _get(self, path, user_id=2, status=200):
        response = self.client.get(path, headers=self.headers.get(user_id, {}))
        self.assertEqual(response.status_code, status, response.get_data(as_text=True))
        return response.get_json()

    def _decision(self, course_id, action, user_id=2, status=200, **payload):
        response = self.client.post(
            f"/api/moderation/courses/{course_id}/{action}",
            headers=self.headers.get(user_id, {}), json=payload,
        )
        self.assertEqual(response.status_code, status, response.get_data(as_text=True))
        return response.get_json()

    def test_only_admin_can_create_or_assign_moderator_accounts(self):
        for user_id in (None, 2, 3, 5):
            expected = 401 if user_id is None else 403
            with self.subTest(user_id=user_id):
                create = self.client.post("/api/users", headers=self.headers.get(user_id, {}), json={
                    "username": "new-moderator", "email": "new-moderator@example.test",
                    "password": "test-password-123", "role": "MODERATOR",
                })
                self.assertEqual(create.status_code, expected)
                assign = self.client.patch(
                    "/api/users/5/role", headers=self.headers.get(user_id, {}), json={"role_id": 2},
                )
                self.assertEqual(assign.status_code, expected)
        create = self.client.post("/api/users", headers=self.headers[1], json={
            "username": "new-moderator", "email": "new-moderator@example.test",
            "password": "test-password-123", "role": "MODERATOR",
        })
        self.assertEqual(create.status_code, 201, create.get_data(as_text=True))
        self.assertEqual(create.get_json()["data"]["role"]["name"], "MODERATOR")
        assign = self.client.patch("/api/users/5/role", headers=self.headers[1], json={"role_id": 2})
        self.assertEqual(assign.status_code, 200)
        self._get("/api/moderation/courses", user_id=5)

    def test_public_registration_cannot_select_moderator_by_name_or_id(self):
        for user_id in (None, 2):
            for selection in ({"role": "MODERATOR"}, {"role_id": 2}):
                with self.subTest(user_id=user_id, selection=selection):
                    response = self.client.post("/api/auth/register", headers=self.headers.get(user_id, {}), json={
                        "username": "self-moderator", "email": "self-moderator@example.test",
                        "password": "test-password-123", **selection,
                    })
                    self.assertEqual(response.status_code, 403)
        with self.app.app_context():
            self.assertIsNone(db.session.scalar(select(User).where(User.username == "self-moderator")))

    def test_former_instructor_is_reported_as_moderator_without_edit_permissions(self):
        user = self._get("/api/auth/me")["data"]
        self.assertEqual(user["role"]["name"], "MODERATOR")
        self.assertFalse(user["is_approved_instructor"])
        for course_id in (1, 4):
            course = self._get(f"/api/courses/{course_id}")["data"]
            self.assertFalse(course["can_manage"])
            self.assertTrue(course["can_access_materials"])
        book = self._get("/api/course-resources/6")["data"]
        self.assertFalse(book["can_manage"])

    def test_non_reviewers_cannot_open_queue_filters_detail_or_decisions(self):
        for user_id in (None, 3, 5):
            status = 401 if user_id is None else 403
            with self.subTest(user_id=user_id):
                for path in ("/api/moderation/filters", "/api/moderation/courses", "/api/moderation/courses/1"):
                    self._get(path, user_id=user_id, status=status)
                for action in ("approve", "reject"):
                    self._decision(1, action, user_id=user_id, status=status, review_version=0, reason="Review")

    def test_pending_and_rejected_courses_and_materials_stay_hidden_from_students(self):
        for user_id in (None, 5):
            with self.subTest(user_id=user_id):
                courses = self._get("/api/courses", user_id=user_id)["data"]
                self.assertEqual({course["id"] for course in courses}, {2})
                department = self._get("/api/courses/department/1", user_id=user_id)["data"]
                self.assertEqual({course["id"] for course in department}, {2})
                for base in ("lectures", "course-resources"):
                    materials = self._get(f"/api/{base}", user_id=user_id)["data"]
                    self.assertFalse(any(item["course_id"] in {1, 3, 4, 5} for item in materials))
                for course_id in (1, 3):
                    for path in (
                        f"/api/courses/{course_id}", f"/api/lectures/{course_id}",
                        f"/api/lectures/course/{course_id}", f"/api/course-resources/{course_id}",
                        f"/api/course-resources/course/{course_id}",
                    ):
                        self._get(path, user_id=user_id, status=404)
                    for filename in ("lecture.txt", "resource.pdf"):
                        response = self.client.get(
                            f"/uploads/courses/{course_id}/{filename}", headers=self.headers.get(user_id, {}),
                        )
                        self.assertEqual(response.status_code, 403)

    def test_moderators_and_admins_can_read_all_course_materials_and_authenticated_files(self):
        for user_id in (1, 2, 6):
            with self.subTest(user_id=user_id):
                for course_id in (1, 2, 3, 4, 5):
                    detail = self._get(f"/api/moderation/courses/{course_id}", user_id=user_id)["data"]
                    self.assertEqual(detail["id"], course_id)
                    self.assertEqual(len(detail["lectures"]), 1)
                    self.assertEqual(len(detail["resources"]), 1)
                    self.assertEqual(detail["review_history"], [])
                    for base in ("lectures", "course-resources"):
                        material = self._get(f"/api/{base}/{course_id}", user_id=user_id)["data"]
                        self.assertFalse(material["locked"])
                    for filename in ("lecture.txt", "resource.pdf"):
                        response = self.client.get(
                            f"/uploads/courses/{course_id}/{filename}", headers=self.headers[user_id],
                        )
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.data, f"Course {course_id} review material".encode())
                        response.close()

    def test_queue_filters_search_and_pagination(self):
        filters = self._get("/api/moderation/filters")["data"]
        self.assertEqual({item["id"] for item in filters["faculties"]}, {1, 2})
        self.assertEqual({item["id"] for item in filters["departments"]}, {1, 2, 3})
        self.assertTrue({3, 4}.issubset({item["id"] for item in filters["instructors"]}))
        cases = (
            ("status=ALL&faculty_id=1", {1, 2, 5}),
            ("status=ALL&department_id=2", {3, 4}),
            ("status=ALL&instructor_id=3", {1, 2}),
            ("status=PENDING&faculty_id=1&instructor_id=4", {5}),
            ("status=APPROVED", {2}), ("status=REJECTED", {3}),
            ("status=ALL&q=algorithms", {1}),
        )
        for query, expected in cases:
            with self.subTest(query=query):
                response = self._get(f"/api/moderation/courses?{query}")
                self.assertEqual({item["id"] for item in response["data"]}, expected)
        first = self._get("/api/moderation/courses?status=ALL&page=1&per_page=2")
        second = self._get("/api/moderation/courses?status=ALL&page=2&per_page=2")
        self.assertEqual(first["pagination"], {"page": 1, "per_page": 2, "total": 5, "pages": 3})
        self.assertEqual(len(second["data"]), 2)
        self.assertFalse({item["id"] for item in first["data"]} & {item["id"] for item in second["data"]})

    def test_invalid_filters_are_rejected(self):
        for query in ("faculty_id=bad", "department_id=-1", "instructor_id=0", "status=INVALID", "page=0"):
            with self.subTest(query=query):
                self._get(f"/api/moderation/courses?{query}", status=400)

    def test_approval_publishes_course_and_records_review_audit(self):
        self._decision(1, "approve", review_version=0, reason="Ready for students")
        detail = self._get("/api/moderation/courses/1")["data"]
        self.assertEqual(detail["status"], "PUBLISHED")
        self.assertEqual(detail["review_status"], "APPROVED")
        self.assertEqual(detail["review_reason"], "Ready for students")
        self.assertEqual(detail["reviewed_by"]["id"], 2)
        self.assertTrue(detail["reviewed_at"])
        self.assertGreater(detail["review_version"], 0)
        self.assertEqual(len(detail["review_history"]), 1)
        history = detail["review_history"][0]
        self.assertEqual(history["status"], "APPROVED")
        self.assertEqual(history["reason"], "Ready for students")
        self.assertEqual(history["reviewed_by"]["id"], 2)
        self.assertTrue(history["reviewed_at"])
        self._get("/api/courses/1", user_id=None)

    def test_rejection_requires_reason_and_preserves_audited_decision_history(self):
        for reason in (None, "", "   "):
            self._decision(1, "reject", status=400, review_version=0, reason=reason)
        self.assertEqual(self._get("/api/moderation/courses/1")["data"]["review_history"], [])
        self._decision(1, "reject", review_version=0, reason="Please provide the missing notes")
        rejected = self._get("/api/moderation/courses/1")["data"]
        self.assertEqual(rejected["status"], "DRAFT")
        self.assertEqual(rejected["review_status"], "REJECTED")
        self.assertEqual(rejected["review_reason"], "Please provide the missing notes")
        self.assertEqual(rejected["reviewed_by"]["id"], 2)
        self.assertTrue(rejected["reviewed_at"])
        self._get("/api/courses/1", user_id=None, status=404)
        self._decision(1, "approve", user_id=1, review_version=rejected["review_version"], reason="Admin reviewed corrections")
        approved = self._get("/api/moderation/courses/1")["data"]
        self.assertEqual(approved["reviewed_by"]["id"], 1)
        self.assertEqual(len(approved["review_history"]), 2)
        history = {entry["status"]: entry for entry in approved["review_history"]}
        self.assertEqual(history["REJECTED"]["reason"], "Please provide the missing notes")
        self.assertEqual(history["REJECTED"]["reviewed_by"]["id"], 2)
        self.assertEqual(history["APPROVED"]["reviewed_by"]["id"], 1)

    def test_missing_and_stale_review_versions_cannot_override_a_review(self):
        self._decision(1, "approve", status=400)
        self._decision(1, "approve", review_version=0)
        self._decision(1, "reject", status=409, review_version=0, reason="Stale decision")
        detail = self._get("/api/moderation/courses/1")["data"]
        self.assertEqual(detail["review_status"], "APPROVED")
        self.assertEqual(len(detail["review_history"]), 1)

    def test_review_payload_cannot_change_course_content_or_spoof_reviewer(self):
        for extra in ({"title": "Changed by moderator"}, {"reviewed_by": 1}, {"status": "PUBLISHED"}):
            with self.subTest(extra=extra):
                response = self.client.post(
                    "/api/moderation/courses/1/approve", headers=self.headers[2],
                    json={"review_version": 0, **extra},
                )
                self.assertEqual(response.status_code, 400, response.get_data(as_text=True))
        self._decision(1, "reject", status=400, review_version=0, reason="x" * 2001)
        detail = self._get("/api/moderation/courses/1")["data"]
        self.assertEqual(detail["title"], "Pending algorithms")
        self.assertEqual(detail["review_history"], [])

    def test_new_instructor_courses_enter_review_even_when_publication_is_requested(self):
        response = self.client.post("/api/courses", headers=self.headers[3], json={
            "department_id": 1, "title": "New instructor course", "slug": "new-instructor-course",
            "status": "PUBLISHED",
        })
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        course = response.get_json()["data"]
        self.assertEqual(course["owner_id"], 3)
        self.assertEqual(course["status"], "DRAFT")
        self.assertEqual(course["review_status"], "PENDING")
        self._get(f"/api/courses/{course['id']}", user_id=None, status=404)
        pending = self._get("/api/moderation/courses?status=PENDING")["data"]
        self.assertIn(course["id"], {item["id"] for item in pending})

    def test_instructor_content_edits_require_a_new_review_and_invalidate_old_version(self):
        for path, payload in (
            ("/api/courses/2", {"description": "Changed introduction"}),
            ("/api/lectures/2", {"title": "Changed lecture"}),
            ("/api/course-resources/2", {"title": "Changed resource"}),
        ):
            with self.subTest(path=path):
                before = self._get("/api/moderation/courses/2")["data"]
                response = self.client.patch(path, headers=self.headers[3], json=payload)
                self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
                after = self._get("/api/moderation/courses/2")["data"]
                self.assertEqual(after["review_status"], "PENDING")
                self.assertEqual(after["status"], "DRAFT")
                self.assertGreater(after["review_version"], before["review_version"])
                self._decision(2, "approve", status=409, review_version=before["review_version"])
                self._decision(2, "approve", review_version=after["review_version"])

    def test_moderator_cannot_mutate_any_non_review_api_even_with_prior_ownership(self):
        checked = 0
        for rule in self.app.url_map.iter_rules():
            if not rule.rule.startswith("/api/") or rule.rule.startswith("/api/auth/"):
                continue
            if rule.rule.startswith("/api/moderation/") and rule.rule.endswith(("/approve", "/reject")):
                continue
            for method in sorted(rule.methods & {"POST", "PUT", "PATCH", "DELETE"}):
                path = re.sub(r"<[^>]+>", "4", rule.rule)
                with self.subTest(method=method, path=path):
                    response = self.client.open(path, method=method, headers=self.headers[2], json={})
                    self.assertEqual(response.status_code, 403, response.get_data(as_text=True))
                checked += 1
        self.assertGreater(checked, 30)
        for method in ("PATCH", "DELETE"):
            response = self.client.open("/api/course-resources/6", method=method, headers=self.headers[2], json={"title": "Not allowed"})
            self.assertEqual(response.status_code, 403)
        upload = self.client.post("/api/uploads", headers=self.headers[2], data={
            "file": (BytesIO(b"not allowed"), "moderator-upload.txt"), "folder": "courses/4",
        }, content_type="multipart/form-data")
        self.assertEqual(upload.status_code, 403)
        self.assertFalse((self.upload_root / "courses/4/moderator-upload.txt").exists())
        with self.app.app_context():
            self.assertEqual(db.session.get(Course, 4).title, "Former instructor course")
            self.assertEqual(db.session.get(CourseResource, 6).title, "Moderator's former book")

    def test_assigned_instructor_keeps_draft_access_after_submitting_changes(self):
        response = self.client.patch(
            "/api/lectures/2", headers=self.headers[4], json={"title": "Assigned instructor changes"},
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        course = self._get("/api/courses/2", user_id=4)["data"]
        self.assertEqual(course["status"], "DRAFT")
        self.assertTrue(course["can_manage"])
        self.assertTrue(course["can_access_materials"])
        self.assertIn(2, {item["id"] for item in self._get("/api/courses", user_id=4)["data"]})
        self._get("/api/lectures/2", user_id=4)
        self._get("/api/lectures/course/2", user_id=4)
        self._get("/api/course-resources/2", user_id=4)
        response = self.client.get("/uploads/courses/2/resource.pdf", headers=self.headers[4])
        self.assertEqual(response.status_code, 200)
        response.close()
        self._get("/api/courses/2", user_id=5, status=404)

    def test_admin_retains_content_edit_upload_and_review_permissions(self):
        response = self.client.patch("/api/courses/1", headers=self.headers[1], json={"title": "Admin correction"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertEqual(response.get_json()["data"]["title"], "Admin correction")
        upload = self.client.post("/api/uploads", headers=self.headers[1], data={
            "file": (BytesIO(b"admin notes"), "admin-upload.txt"), "folder": "courses/1",
        }, content_type="multipart/form-data")
        self.assertEqual(upload.status_code, 200, upload.get_data(as_text=True))
        detail = self._get("/api/moderation/courses/1", user_id=1)["data"]
        self._decision(1, "approve", user_id=1, review_version=detail["review_version"])

    def test_legacy_admin_publication_records_matching_review_versions(self):
        created = self.client.post("/api/courses", headers=self.headers[1], json={
            "title": "Admin published course", "slug": "admin-published-course", "department_id": 1,
            "status": "PUBLISHED",
        })
        self.assertEqual(created.status_code, 201, created.get_data(as_text=True))
        course_id = created.get_json()["data"]["id"]
        first = self._get(f"/api/moderation/courses/{course_id}")["data"]
        self.assertEqual(first["review_status"], "APPROVED")
        self.assertEqual(first["review_history"][0]["review_version"], first["review_version"])
        self._get(f"/api/courses/{course_id}", user_id=None)
        for title in ("Admin correction one", "Admin correction two"):
            response = self.client.patch(f"/api/courses/{course_id}", headers=self.headers[1], json={
                "title": title, "status": "PUBLISHED",
            })
            self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        reviewed = self._get(f"/api/moderation/courses/{course_id}")["data"]
        self.assertEqual(reviewed["review_version"], first["review_version"] + 2)
        self.assertEqual(len(reviewed["review_history"]), 3)
        self.assertEqual(reviewed["review_history"][0]["review_version"], reviewed["review_version"])
        self.assertEqual(reviewed["review_history"][0]["reviewed_by"]["id"], 1)

    def test_moving_materials_authorizes_both_courses_and_invalidates_both_previews(self):
        for collection in ("lectures", "course-resources"):
            with self.subTest(collection=collection):
                # Alice cannot move another owner's material into her own course.
                forbidden = self.client.patch(f"/api/{collection}/3", headers=self.headers[3], json={"course_id": 1})
                self.assertEqual(forbidden.status_code, 403, forbidden.get_data(as_text=True))
                # Nor can she place her own material in somebody else's course.
                forbidden = self.client.patch(f"/api/{collection}/1", headers=self.headers[3], json={"course_id": 3})
                self.assertEqual(forbidden.status_code, 403, forbidden.get_data(as_text=True))
                before = {course_id: self._get(f"/api/moderation/courses/{course_id}")["data"]["review_version"] for course_id in (1, 2)}
                payload = {"course_id": 2}
                if collection == "lectures":
                    payload["lecture_number"] = 2
                moved = self.client.patch(f"/api/{collection}/1", headers=self.headers[3], json=payload)
                self.assertEqual(moved.status_code, 200, moved.get_data(as_text=True))
                self.assertEqual(moved.get_json()["data"]["course_id"], 2)
                for course_id in (1, 2):
                    after = self._get(f"/api/moderation/courses/{course_id}")["data"]
                    self.assertEqual(after["status"], "DRAFT")
                    self.assertEqual(after["review_status"], "PENDING")
                    self.assertGreater(after["review_version"], before[course_id])
                    self._decision(course_id, "approve", review_version=before[course_id], status=409)

    def test_upload_path_aliases_cannot_expose_unapproved_material(self):
        for path in (
            "/uploads/unused/../courses/1/resource.pdf",
            "/uploads/courses/2/../1/resource.pdf",
            "/uploads/COURSES/1/RESOURCE.PDF",
            "/uploads/unused/../courses/3/lecture.txt",
        ):
            for user_id in (None, 5):
                with self.subTest(path=path, user_id=user_id):
                    response = self.client.get(path, headers=self.headers.get(user_id, {}))
                    self.assertEqual(response.status_code, 403, response.get_data(as_text=True))
        for path in ("/uploads/../../config.py", "/uploads/courses/1/../../../config.py"):
            response = self.client.get(path, headers=self.headers[2])
            self.assertEqual(response.status_code, 404)
