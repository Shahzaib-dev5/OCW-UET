"""Password authentication with temporarily optional email OTP verification."""
from unittest import TestCase
from unittest.mock import patch

import test_moderation_api as fixtures
from app.extensions import db
from app.models.user import User
from sqlalchemy import select


class OptionalEmailOtpTests(TestCase):
    setUp = fixtures.ModerationApiTests.setUp
    tearDown = fixtures.ModerationApiTests.tearDown

    def signup(self):
        return self.client.post("/api/auth/register", json={
            "email": "new-student@example.test",
            "password": "StrongPassword123",
            "full_name": "New Student",
            "cnic": "1234512345671",
            "gender": "MALE",
            "university_name": "UET",
            "department_name": "Computing",
            "academic_status": "GRADUATE",
        })

    def login(self, password="StrongPassword123"):
        return self.client.post("/api/auth/login", json={
            "email": "new-student@example.test", "password": password,
        })

    def test_disabled_signup_and_login_do_not_need_email_service(self):
        self.app.config["EMAIL_OTP_ENABLED"] = False
        with patch("app.routes.auth._send_email_otp") as mail:
            response = self.signup()
            self.assertEqual(response.status_code, 201)
            self.assertFalse(response.json["verification_required"])
            self.assertTrue(response.json["access_token"])
            self.assertEqual(self.login().status_code, 200)
            mail.assert_not_called()
        with self.app.app_context():
            user = db.session.scalar(select(User).where(User.email == "new-student@example.test"))
            self.assertFalse(user.email_verified)
            self.assertIsNone(user.email_otp_hash)
        self.assertEqual(self.login("wrong-password").status_code, 401)

    def test_disabled_otp_endpoints_cannot_issue_tokens(self):
        self.app.config["EMAIL_OTP_ENABLED"] = False
        for endpoint in ("verify-email-otp", "resend-email-otp"):
            response = self.client.post(f"/api/auth/{endpoint}", json={"email": "admin@example.test", "otp": "000000"})
            self.assertEqual(response.status_code, 409)
            self.assertNotIn("access_token", response.json)

    def test_reenable_restores_verification_gate(self):
        self.app.config["EMAIL_OTP_ENABLED"] = True
        with patch("app.routes.auth._send_email_otp", return_value=True) as mail:
            response = self.signup()
            self.assertEqual(response.status_code, 201)
            self.assertTrue(response.json["verification_required"])
            self.assertNotIn("access_token", response.json)
            otp = mail.call_args.args[1]
        self.assertEqual(self.login().status_code, 403)
        verified = self.client.post("/api/auth/verify-email-otp", json={"email": "new-student@example.test", "otp": otp})
        self.assertEqual(verified.status_code, 200)
        self.assertEqual(self.login().status_code, 200)
        replay = self.client.post("/api/auth/verify-email-otp", json={"email": "new-student@example.test", "otp": "000000"})
        self.assertEqual(replay.status_code, 409)

    def test_existing_unverified_login_and_inactive_account(self):
        self.app.config["EMAIL_OTP_ENABLED"] = True
        self.assertEqual(self.signup().status_code, 201)
        self.app.config["EMAIL_OTP_ENABLED"] = False
        self.assertEqual(self.login().status_code, 200)
        with self.app.app_context():
            user = db.session.scalar(select(User).where(User.email == "new-student@example.test"))
            user.is_active = False
            db.session.commit()
        self.assertEqual(self.login().status_code, 403)
