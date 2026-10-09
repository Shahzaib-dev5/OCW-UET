import os
import re
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.services.authz import current_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

DEFAULT_ROLE_DESCRIPTIONS = {
    "ADMIN": "Full access to all OCW management APIs",
    "TEACHER": "Can apply to teach courses and manage resources for approved courses",
    "STUDENT": "Can apply for courses and view resources after approval",
}


@auth_bp.route("/health", methods=["GET"])
def auth_health():
    return jsonify({
        "status": "success",
        "message": "Auth API is working"
    })


@auth_bp.route("/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)
    unknown_fields = set(payload) - {
        "username", "email", "password", "password_confirmation", "role", "role_id", "full_name", "return_to",
        "date_of_birth", "cnic", "gender", "university_name", "department_name", "academic_status", "semester",
    }
    if unknown_fields:
        return _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    required_fields = ["email", "password"]
    for field in required_fields:
        if field not in payload:
            return _error(f"{field} is required", 400)
    if payload.get("password_confirmation") is not None and payload.get("password") != payload.get("password_confirmation"):
        return _error("password confirmation does not match", 400)
    if len(str(payload.get("password") or "")) < 8:
        return _error("password must be at least 8 characters", 400)

    role, error = _role_from_payload(payload)
    if error:
        return error

    profile_values, error = _profile_values(payload)
    if error:
        return error

    email = payload["email"].strip().lower()
    username = (payload.get("username") or email.split("@")[0]).strip()
    otp = _new_otp()
    user = User(
        role_id=role.id,
        username=username,
        email=email,
        password_hash=generate_password_hash(payload["password"]),
        full_name=payload.get("full_name") or username,
        email_verified=False,
        email_otp_hash=generate_password_hash(otp),
        email_otp_expires_at=datetime.utcnow() + timedelta(minutes=10),
        email_otp_attempts=0,
        **profile_values,
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Username, email, or CNIC already exists", 409)
    if not _send_email_otp(user.email, otp):
        return _error("Email OTP service is not configured", 503)

    response = {
        "status": "success",
        "message": "Account created. Verify the OTP sent to your email before login.",
        "verification_required": True,
        "email": user.email,
        "return_to": payload.get("return_to"),
    }
    _attach_dev_otp(response, otp)
    return jsonify(response), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)
    unknown_fields = set(payload) - {"email", "username", "password"}
    if unknown_fields:
        return _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    login_value = payload.get("email") or payload.get("username")
    password = payload.get("password")
    if not isinstance(login_value, str) or not login_value.strip():
        return _error("email or username is required", 400)
    if not isinstance(password, str) or not password:
        return _error("password is required", 400)

    user = db.session.scalar(
        select(User).where((User.email == login_value.strip()) | (User.username == login_value.strip()))
    )
    if user is None or not check_password_hash(user.password_hash, password):
        return _error("Invalid email/username or password", 401)
    if not user.is_active:
        return _error("User account is inactive", 403)
    if not user.email_verified:
        return _error("Email verification required. Please verify your OTP before login.", 403)

    user.last_login = datetime.utcnow()
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Email, Google account, or CNIC already exists", 409)

    token = create_access_token(identity=str(user.id))
    return jsonify({"status": "success", "access_token": token, "data": _serialize_user(user)})


@auth_bp.route("/google", methods=["POST"])
def google_auth():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)
    credential = payload.get("credential") or payload.get("id_token")
    if not isinstance(credential, str) or not credential.strip():
        return _error("Google credential is required", 400)

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        return _error("Google OAuth is not configured on the server", 503)

    try:
        claims = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id,
        )
    except ValueError:
        return _error("Invalid Google credential", 401)

    email = (claims.get("email") or "").strip().lower()
    google_sub = claims.get("sub")
    if not email or not google_sub:
        return _error("Google credential did not include an email identity", 400)
    if not claims.get("email_verified"):
        return _error("Google account email must be verified", 403)
    profile_values, error = _optional_profile_values(payload, email=email)
    if error:
        return error

    user = db.session.scalar(select(User).where(User.google_sub == google_sub))
    linked = False
    if user is None:
        user = db.session.scalar(select(User).where(User.email == email))
        if user is not None:
            if user.email_verified and user.google_sub not in {None, google_sub}:
                return _error("This email is already linked to another Google account", 409)
            user.google_sub = google_sub
            user.email_verified = True
            user.email_otp_hash = None
            user.email_otp_expires_at = None
            user.email_otp_attempts = 0
            linked = True

    if user is None:
        role, error = _role_from_payload({"role": "STUDENT"})
        if error:
            return error
        username = _unique_username(email.split("@")[0])
        user = User(
            role_id=role.id,
            username=username,
            email=email,
            password_hash=generate_password_hash(secrets.token_urlsafe(32)),
            full_name=claims.get("name") or username,
            auth_provider="google",
            google_sub=google_sub,
            email_verified=True,
            email_otp_hash=None,
            email_otp_expires_at=None,
            email_otp_attempts=0,
            **profile_values,
        )
        db.session.add(user)
    elif not user.is_active:
        return _error("User account is inactive", 403)
    elif profile_values:
        for field, value in profile_values.items():
            if value not in {None, ""}:
                setattr(user, field, value)

    user.last_login = datetime.utcnow()
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("Email, Google account, or CNIC already exists", 409)
    token = create_access_token(identity=str(user.id))
    return jsonify({"status": "success", "access_token": token, "linked": linked, "data": _serialize_user(user), "return_to": payload.get("return_to")})


@auth_bp.route("/verify-email-otp", methods=["POST"])
def verify_email_otp():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)
    unknown_fields = set(payload) - {"email", "otp", "return_to"}
    if unknown_fields:
        return _error(f"Unknown fields: {', '.join(sorted(unknown_fields))}", 400)

    email = str(payload.get("email") or "").strip().lower()
    otp = str(payload.get("otp") or "").strip()
    if not email or not otp:
        return _error("email and otp are required", 400)

    user = db.session.scalar(select(User).where(User.email == email))
    if user is None:
        return _error("Invalid or expired OTP", 400)
    if user.email_verified:
        token = create_access_token(identity=str(user.id))
        return jsonify({"status": "success", "access_token": token, "data": _serialize_user(user), "return_to": payload.get("return_to")})
    if not user.email_otp_hash or not user.email_otp_expires_at or user.email_otp_expires_at < datetime.utcnow():
        return _error("Invalid or expired OTP", 400)
    if user.email_otp_attempts >= 5:
        return _error("Too many OTP attempts. Request a new OTP.", 429)
    if not check_password_hash(user.email_otp_hash, otp):
        user.email_otp_attempts = (user.email_otp_attempts or 0) + 1
        db.session.commit()
        return _error("Invalid or expired OTP", 400)

    user.email_verified = True
    user.email_otp_hash = None
    user.email_otp_expires_at = None
    user.email_otp_attempts = 0
    user.last_login = datetime.utcnow()
    db.session.commit()
    token = create_access_token(identity=str(user.id))
    return jsonify({"status": "success", "access_token": token, "data": _serialize_user(user), "return_to": payload.get("return_to")})


@auth_bp.route("/resend-email-otp", methods=["POST"])
def resend_email_otp():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a JSON object", 400)
    email = str(payload.get("email") or "").strip().lower()
    if not email:
        return _error("email is required", 400)

    user = db.session.scalar(select(User).where(User.email == email))
    response = {"status": "success", "message": "If verification is pending, a new OTP can be sent."}
    if user is not None and not user.email_verified:
        otp = _new_otp()
        user.email_otp_hash = generate_password_hash(otp)
        user.email_otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
        user.email_otp_attempts = 0
        db.session.commit()
        if not _send_email_otp(user.email, otp):
            return _error("Email OTP service is not configured", 503)
        _attach_dev_otp(response, otp)
    return jsonify(response)


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email") or "").strip().lower()
    if not email:
        return _error("email is required", 400)
    user = db.session.scalar(select(User).where(User.email == email))
    reset_token = None
    if user is not None:
        reset_token = secrets.token_urlsafe(32)
        user.reset_token_hash = generate_password_hash(reset_token)
        user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
    response = {"status": "success", "message": "If the account exists, a password reset link can be sent."}
    if os.getenv("FLASK_ENV") != "production" and reset_token:
        response["reset_token"] = reset_token
    return jsonify(response)


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    payload = request.get_json(silent=True) or {}
    token = payload.get("token")
    password = payload.get("password")
    if not token or not password:
        return _error("token and password are required", 400)
    if payload.get("password_confirmation") is not None and password != payload.get("password_confirmation"):
        return _error("password confirmation does not match", 400)
    if len(str(password)) < 8:
        return _error("password must be at least 8 characters", 400)
    users = db.session.scalars(select(User).where(User.reset_token_hash.isnot(None))).all()
    user = next((item for item in users if item.reset_token_expires_at and item.reset_token_expires_at >= datetime.utcnow() and check_password_hash(item.reset_token_hash, token)), None)
    if user is None:
        return _error("Invalid or expired reset token", 400)
    user.password_hash = generate_password_hash(password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.session.commit()
    return jsonify({"status": "success", "message": "Password has been reset"})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    return jsonify({"status": "success", "message": "Logged out"})


@auth_bp.route("/me", methods=["GET"])
def me():
    user = current_user()
    if user is None:
        return _error("Authentication required", 401)
    return jsonify({"status": "success", "data": _serialize_user(user)})


def _role_from_payload(payload):
    role_id = payload.get("role_id")
    role_name = payload.get("role")

    if role_id is not None:
        if not isinstance(role_id, int) or role_id <= 0:
            return None, _error("role_id must be a positive integer", 400)
        role = db.session.get(Role, role_id)
    else:
        role_name = role_name or "STUDENT"
        if not isinstance(role_name, str) or not role_name.strip():
            return None, _error("role must be a non-empty string", 400)
        role = db.session.scalar(select(Role).where(Role.name == role_name.strip().upper()))

    if role is None:
        if role_name and role_name.strip().upper() in DEFAULT_ROLE_DESCRIPTIONS:
            normalized_role = role_name.strip().upper()
            role = Role(name=normalized_role, description=DEFAULT_ROLE_DESCRIPTIONS[normalized_role])
            db.session.add(role)
            db.session.flush()
        else:
            return None, _error("Role not found. Use role ADMIN, TEACHER, or STUDENT", 404)
    logged_in_user = current_user()
    logged_in_role = logged_in_user.role.name if logged_in_user and logged_in_user.role else None
    if role.name != "STUDENT" and logged_in_role != "ADMIN":
        return None, _error("Only an admin can create non-student accounts", 403)
    if role.name == "ADMIN" and _admin_exists() and logged_in_role != "ADMIN":
        return None, _error("Only an existing admin can create another admin account", 403)
    return role, None


def _admin_exists():
    return db.session.scalar(
        select(User)
        .join(Role)
        .where(Role.name == "ADMIN")
        .limit(1)
    ) is not None


def _serialize_user(user):
    return {
        "id": user.id,
        "role_id": user.role_id,
        "role": {
            "id": user.role.id,
            "name": user.role.name,
            "description": user.role.description,
        } if user.role else None,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
        "cnic_masked": _mask_cnic(user.cnic),
        "gender": user.gender,
        "university_name": user.university_name,
        "department_name": user.department_name,
        "academic_status": user.academic_status,
        "semester": user.semester,
        "is_active": user.is_active,
        "auth_provider": user.auth_provider,
        "email_verified": user.email_verified,
        "instructor_status": user.instructor_status,
        "is_approved_instructor": (user.instructor_status or "").upper() == "APPROVED",
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def _error(message, status_code):
    return jsonify({"status": "error", "message": message}), status_code


def _unique_username(base):
    candidate = "".join(ch for ch in str(base or "student").lower() if ch.isalnum() or ch in {"_", "-"}) or "student"
    current = candidate
    suffix = 1
    while db.session.scalar(select(User).where(User.username == current)) is not None:
        suffix += 1
        current = f"{candidate}{suffix}"
    return current


def _profile_values(payload):
    full_name = str(payload.get("full_name") or "").strip()
    if not full_name:
        return None, _error("full_name is required", 400)

    email = str(payload.get("email") or "").strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return None, _error("email must be a valid email address", 400)

    date_of_birth = None
    if payload.get("date_of_birth"):
        try:
            date_of_birth = datetime.strptime(str(payload["date_of_birth"]), "%Y-%m-%d").date()
        except ValueError:
            return None, _error("date_of_birth must use YYYY-MM-DD format", 400)

    cnic = _normalize_cnic(payload.get("cnic"))
    if not cnic:
        return None, _error("cnic is required", 400)

    gender = _clean_choice(payload.get("gender"), {"MALE", "FEMALE", "OTHER", "PREFER_NOT_TO_SAY"}, "gender")
    if isinstance(gender, tuple):
        return None, gender[1]

    academic_status = _clean_choice(payload.get("academic_status"), {"SEMESTER", "GRADUATE"}, "academic_status")
    if isinstance(academic_status, tuple):
        return None, academic_status[1]

    university_name = str(payload.get("university_name") or "").strip()
    department_name = str(payload.get("department_name") or "").strip()
    if not university_name:
        return None, _error("university_name is required", 400)
    if not department_name:
        return None, _error("department_name is required", 400)

    semester = str(payload.get("semester") or "").strip() or None
    if academic_status == "SEMESTER" and not semester:
        return None, _error("semester is required for current semester students", 400)

    return {
        "date_of_birth": date_of_birth,
        "cnic": cnic,
        "gender": gender,
        "university_name": university_name,
        "department_name": department_name,
        "academic_status": academic_status,
        "semester": semester,
    }, None


def _optional_profile_values(payload, email=None):
    profile_fields = {"date_of_birth", "cnic", "gender", "university_name", "department_name", "academic_status", "semester"}
    if not any(payload.get(field) for field in profile_fields):
        return {}, None

    values, error = _profile_values({
        **payload,
        "email": email or payload.get("email"),
        "full_name": payload.get("full_name") or payload.get("name") or "Google User",
    })
    return values or {}, error


def _normalize_cnic(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) != 13:
        return None
    return f"{digits[:5]}-{digits[5:12]}-{digits[12]}"


def _clean_choice(value, allowed, field_name):
    normalized = str(value or "").strip().upper()
    if normalized not in allowed:
        return None, _error(f"{field_name} must be one of: {', '.join(sorted(allowed))}", 400)
    return normalized


def _new_otp():
    return f"{secrets.randbelow(900000) + 100000}"


def _attach_dev_otp(response, otp):
    if os.getenv("FLASK_ENV") != "production":
        response["otp"] = otp


def _send_email_otp(email, otp):
    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM") or username
    if not host or not sender:
        return os.getenv("FLASK_ENV") != "production"

    port = int(os.getenv("SMTP_PORT") or "587")
    use_ssl = os.getenv("SMTP_SSL", "").lower() in {"1", "true", "yes"}
    message = EmailMessage()
    message["Subject"] = "Your OCW verification code"
    message["From"] = sender
    message["To"] = email
    message.set_content(f"Your OCW verification code is {otp}. It expires in 10 minutes.")

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=10) as smtp:
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=10) as smtp:
                smtp.starttls()
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(message)
    except OSError:
        return False
    return True


def _mask_cnic(cnic):
    if not cnic:
        return None
    digits = "".join(ch for ch in cnic if ch.isdigit())
    if len(digits) != 13:
        return "***"
    return f"{digits[:5]}-*******-{digits[-1]}"
