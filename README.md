# UET Open Courseware

UET Open Courseware is a full-stack open courseware platform for managing and publishing academic course content, departments, faculty, research papers, skills development programs, lectures, media, users, roles, and course enrollment workflows.

The project contains a Flask REST API backend and a React/Vite frontend.

## Project Structure

```text
opencourseware/
  uet-ocw-backend/     Flask API, models, migrations, SQL updates, uploads service
  uet-ocw-frontend/    React frontend built with Vite
  uet_ocw_backup.sql   Database backup/export for local restoration
```

## Features

- Public OCW pages for courses, departments, research, and skills development
- Course detail pages with lectures and downloadable resources
- Research publication listing and detail pages
- Skills development listing, detail pages, thumbnails, and resource downloads
- Flask REST API with JWT authentication
- Student email/password signup, Google sign-in, password reset tokens, enrollment requests, and instructor applications
- Public/restricted access controls for courses, course books, and skills development resources
- Role, permission, user, menu, media, faculty, department, course, lecture, author, and upload APIs
- Backend moderator dashboard for reviewing instructor courses and materials, with faculty, department, and instructor filters
- MySQL database support through SQLAlchemy and Flask-Migrate
- Built-in API health endpoint and OpenAPI/Swagger documentation

## Tech Stack

- Frontend: React, Vite, React Router
- Backend: Python, Flask, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-CORS
- Database: MySQL
- API Docs: OpenAPI/Swagger UI

## Requirements

- Node.js and npm
- Python 3.10+
- MySQL

## Backend Setup

```bash
cd uet-ocw-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Update `.env` with your local MySQL database credentials before starting the backend.

Default backend URL:

```text
http://127.0.0.1:5001
```

Useful backend routes:

```text
GET /api/health
GET /apidocs
GET /openapi.json
```

## Frontend Setup

```bash
cd uet-ocw-frontend
npm install
npm run dev
```

For local development, keep `uet-ocw-frontend/.env` blank so Vite proxies API requests to the local backend:

```env
VITE_API_BASE_URL=
```

The production frontend build uses `uet-ocw-frontend/.env.production`, currently pointing at `http://10.10.250.163:9999`.

Build the frontend for production:

```bash
npm run build
```

## Database

Restore `uet_ocw_backup.sql` into your MySQL database if you want to seed a local environment from the included backup.

Additional SQL update scripts are available in:

```text
uet-ocw-backend/sql/
```

Apply the student authentication and enrollment migration on an existing MySQL database with:

```bash
mysql -u <user> -p <database> < uet-ocw-backend/sql/2026_10_07_student_auth_enrollment_instructors.sql
```

Existing content is preserved and defaults to `PUBLIC` unless an admin later changes a course, book resource, or skills development program to `RESTRICTED`.

## Course Moderation

Apply `uet-ocw-backend/sql/2026_10_19_course_moderation.sql` to an existing MySQL database before running the updated backend. The migration adds the `MODERATOR` role, course review metadata, and review history while preserving course content and existing publication states.

To provision a moderator, sign in at `/admin/login`, open **Credentials**, choose **Add credentials**, and select **MODERATOR**. Only an admin can create or assign this role. The moderator signs in through the same login page and is redirected to `/moderator/dashboard`.

The review dashboard provides:

- A queue with faculty, department, instructor, review status, and text search filters.
- The submitting instructor's name and email alongside the course's faculty and department.
- A read-only course preview, including its image, descriptions, syllabus, calendar, lectures, and uploaded resources.
- **Approve** and **Reject** actions. Rejection requires a reason, and decisions record the reviewer and time.

Moderators cannot add, edit, delete, upload, manage users, or change permissions. These restrictions are enforced by the API as well as the dashboard. Admins retain their existing management permissions and can access the review dashboard through **Content review**.

New instructor courses and subsequent changes to their course details or materials enter the pending queue. Pending and rejected courses remain hidden from students and public visitors. Approval publishes the course under its existing public/restricted access settings. If the content changes while a reviewer has it open, the reviewer must reload it before deciding.

Review API endpoints (Bearer authentication required):

```text
GET  /api/moderation/filters
GET  /api/moderation/courses
GET  /api/moderation/courses/<course_id>
POST /api/moderation/courses/<course_id>/approve
POST /api/moderation/courses/<course_id>/reject
```

The queue accepts `faculty_id`, `department_id`, `instructor_id`, `status`, `q`, `page`, and `per_page`. Decisions include the current `review_version` from the course preview and an optional `reason` (required for rejection). A stale version returns HTTP 409 without changing the course.

## Google OAuth

Email OTP verification is temporarily disabled by default. Password signup signs users in immediately, and existing unverified accounts can sign in with their password. No OTP is generated or emailed while disabled. To restore verification, set `EMAIL_OTP_ENABLED=true` in the backend environment and restart the backend. Email addresses are not marked verified merely because verification is disabled.

Create a Google OAuth web client in Google Cloud Console, add your frontend origin to the authorized JavaScript origins, then set:

```env
# backend .env
GOOGLE_CLIENT_ID=your-google-web-client-id.apps.googleusercontent.com

# frontend .env
VITE_GOOGLE_CLIENT_ID=your-google-web-client-id.apps.googleusercontent.com
```

The frontend sends the Google ID token to `/api/auth/google`; the backend verifies the token, requires a verified Google email, links only matching verified accounts, and creates new users as students.

## Git Notes

Generated files and local-only folders are ignored, including:

- `node_modules/`
- `venv/`
- `.env`
- `__pycache__/`
- frontend `dist/`
- backend runtime uploads

Do not commit real credentials. Use `.env.example` as the template for local environment variables.
