# UET OCW Free Deployment Roadmap

This roadmap takes the current project live using free or no-cost starter services.

Recommended stack:

- Frontend: Vercel free hosting for the React/Vite app.
- Backend: Render free web service for the Flask API.
- Database: Aiven free MySQL, because this codebase already uses MySQL/PyMySQL.
- Uploads: use external links first, or patch uploads to store Google Drive/Cloudinary URLs before relying on file upload in production.

Important free-tier limits:

- Render free backend services sleep after inactivity, so the first request after a quiet period can be slow.
- Render free filesystem is ephemeral. Files uploaded into the backend container can disappear after redeploys/restarts.
- Aiven free MySQL is good for small projects/prototypes, with limited storage/resources.

Useful references checked October 1, 2026:

- Render free services: https://render.com/docs/free
- Render Flask deployment: https://render.com/docs/deploy-flask
- Aiven free MySQL: https://aiven.io/docs/products/mysql/concepts/mysql-free-tier
- Vite static deployment: https://vite.dev/guide/static-deploy.html

## 1. Prepare The Repository

1. Push this full repository to GitHub.
2. Make sure these folders are committed:
   - `uet-ocw-backend`
   - `uet-ocw-frontend`
   - `uet-ocw-backend/sql`
3. Do not commit `.env`, database passwords, JWT secrets, service account JSON files, or real API keys.

## 2. Create A Free MySQL Database

Use Aiven MySQL free tier.

1. Create an Aiven account.
2. Create a free MySQL service.
3. Open the service overview and copy:
   - Host
   - Port
   - Database name
   - Username
   - Password
   - CA certificate if Aiven requires SSL for your connection.

If Aiven requires SSL and the backend cannot connect, update `uet-ocw-backend/config.py` later to support SSL options. Try the normal DB variables first.

## 3. Export Local Database

From your local machine, export your existing `ocw` database:

```powershell
C:\xampp\mysql\bin\mysqldump.exe -uroot ocw > ocw_export.sql
```

If you only want schema without existing data:

```powershell
C:\xampp\mysql\bin\mysqldump.exe -uroot --no-data ocw > ocw_schema.sql
```

## 4. Import Database Into Aiven

Use the connection details from Aiven:

```powershell
C:\xampp\mysql\bin\mysql.exe -h YOUR_AIVEN_HOST -P YOUR_AIVEN_PORT -u YOUR_AIVEN_USER -p YOUR_AIVEN_DATABASE < ocw_export.sql
```

If PowerShell blocks `<`, use `cmd.exe`:

```powershell
cmd.exe /c "C:\xampp\mysql\bin\mysql.exe -h YOUR_AIVEN_HOST -P YOUR_AIVEN_PORT -u YOUR_AIVEN_USER -p YOUR_AIVEN_DATABASE < ocw_export.sql"
```

Then verify:

```powershell
C:\xampp\mysql\bin\mysql.exe -h YOUR_AIVEN_HOST -P YOUR_AIVEN_PORT -u YOUR_AIVEN_USER -p -e "SHOW TABLES;" YOUR_AIVEN_DATABASE
```

Confirm the `invited_talks` table exists.

## 5. Deploy Backend On Render

1. Go to Render.
2. Create a new Web Service.
3. Connect your GitHub repository.
4. Set:
   - Root Directory: `uet-ocw-backend`
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app`
5. Add environment variables:

```env
FLASK_ENV=production
SECRET_KEY=make-a-long-random-secret
JWT_SECRET_KEY=make-another-long-random-secret

DB_HOST=YOUR_AIVEN_HOST
DB_PORT=YOUR_AIVEN_PORT
DB_NAME=YOUR_AIVEN_DATABASE
DB_USER=YOUR_AIVEN_USER
DB_PASSWORD=YOUR_AIVEN_PASSWORD

UPLOAD_FOLDER=/tmp/uploads
```

Optional Google Drive variables, only if you patch uploads to use the returned Drive URL:

```env
GOOGLE_DRIVE_ROOT_FOLDER_NAME=OCW RES
GOOGLE_DRIVE_PARENT_FOLDER_ID=your-folder-id
GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON=your-json-content-or-path
```

6. Deploy.
7. After deploy, open:

```text
https://YOUR-BACKEND.onrender.com/api/health
```

Expected response:

```json
{
  "status": "success",
  "message": "UET Open Courseware API is running"
}
```

## 6. Check Backend Admin

Open:

```text
https://YOUR-BACKEND.onrender.com/admin/login
```

Create the first admin if needed.

Then open:

```text
https://YOUR-BACKEND.onrender.com/admin/dashboard
```

Verify these sections:

- Courses
- Skills Development
- Invited Talks
- Research Papers
- Lectures & Resources

## 7. Handle Uploads Safely

Current behavior:

- Uploaded files are saved under the backend upload folder.
- In Render free hosting, that folder is temporary.
- This means uploads may work briefly, then disappear after redeploy/restart.

Safe free options:

1. Use external URLs in admin forms for now:
   - Video upload link: YouTube, Google Drive public link, OneDrive public link.
   - File links: Google Drive public link or another permanent file URL.
2. Patch backend upload routes later so `upload_url`, `pdf_url`, `thumbnail`, and resource files store cloud URLs instead of local `/uploads/...` paths.
3. If using Cloudinary free tier, add Cloudinary upload support and save secure URLs.

Do not depend on Render local uploads for important files.

## 8. Deploy Frontend On Vercel

1. Go to Vercel.
2. Import the same GitHub repository.
3. Set:
   - Framework Preset: Vite
   - Root Directory: `uet-ocw-frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Add environment variable:

```env
VITE_API_BASE_URL=https://YOUR-BACKEND.onrender.com
```

5. Deploy.

## 9. Verify Frontend Pages

Open your Vercel URL and test:

```text
/
/courses
/skills-development
/invited-talks
/research
```

Open browser DevTools Network tab and confirm API requests go to:

```text
https://YOUR-BACKEND.onrender.com/api/...
```

## 10. Fix Common Issues

Backend says database unavailable:

- Check Render env vars.
- Check Aiven host, port, username, password, and database name.
- Check whether Aiven requires SSL.

Frontend loads but data is empty:

- Check `VITE_API_BASE_URL` in Vercel.
- Redeploy frontend after changing env vars.
- Open backend `/api/health` directly.

Admin login fails:

- Confirm database was imported.
- Use `/admin/login` first admin setup if no admin exists.

Uploads disappear:

- Expected on free Render local storage.
- Use external file URLs or patch cloud uploads before production use.

CORS errors:

- Current backend enables Flask-CORS globally.
- If you later restrict CORS, allow your Vercel domain.

## 11. Final Production Checklist

Before sharing publicly:

- Use strong `SECRET_KEY` and `JWT_SECRET_KEY`.
- Remove local `.env` secrets from Git.
- Confirm `/admin/dashboard` is protected by admin login.
- Create at least one admin user.
- Test create/edit/delete for:
  - Courses
  - Skills Development
  - Invited Talks
  - Research Papers
- Test frontend pages on mobile and desktop.
- Decide a permanent upload strategy.
- Keep a database backup from Aiven.

## 12. Suggested Next Code Improvements

These are not required to get live, but they will make hosting cleaner:

1. Add `DATABASE_URL` support in `config.py`.
2. Add SSL options for hosted MySQL.
3. Store uploaded cloud URLs instead of local `/uploads/...` URLs.
4. Add a real migration tool flow with Flask-Migrate/Alembic.
5. Add a `render.yaml` blueprint for repeatable backend deploys.
6. Add frontend `vercel.json` rewrite fallback for single-page routing if direct route refreshes fail.
