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

To point the frontend to a backend URL, create `uet-ocw-frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:5001
```

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

## Google OAuth

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
