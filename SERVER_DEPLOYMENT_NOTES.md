# OCW-UET Server Deployment Notes

Last updated: 2026-11-25

This document records the production server layout and the deployment performed on 2026-11-25. Passwords and other credentials are intentionally excluded.

## Server Layout

- Server IP: `10.10.250.163`
- SSH user used by the operator: `careeradmin`
- Public application URL: `http://10.10.250.163:5202`
- Nginx listener: `0.0.0.0:5202`
- Nginx frontend root: `/var/www/ocw-uet`
- Repository: `/home/careeradmin/OCW-UET`
- Backend directory: `/home/careeradmin/OCW-UET/uet-ocw-backend`
- Frontend directory: `/home/careeradmin/OCW-UET/uet-ocw-frontend`
- Backend systemd service: `ocw-uet-backend.service`
- Backend service working directory: `/home/careeradmin/OCW-UET/uet-ocw-backend`
- Backend entry point: `venv/bin/python run.py`
- MySQL database: `uet_ocw`

## Deployment Recorded on 2026-11-25

- Git branch: `main`
- Deployed commit: `f12a78e` (`Add invited talk editing and resources`)
- Code was updated with a fast-forward pull from `origin/main`.
- The frontend production environment file had been handled as a server-local file.
- Backend Python requirements were installed from `uet-ocw-backend/requirements.txt`.
- Frontend dependencies were installed with `npm ci`.
- Frontend was built with `npm run build`.
- Built frontend files were synchronized from `dist/` to `/var/www/ocw-uet/`.
- The backend service was restarted successfully.

## Database Migrations Applied

The following migrations were applied to `uet_ocw` in this order:

1. `uet-ocw-backend/sql/2026_10_19_course_moderation.sql`
2. `uet-ocw-backend/sql/2026_11_20_department_book_resources.sql`
3. `uet-ocw-backend/sql/add_invited_talk_resources.sql`
4. `uet-ocw-backend/sql/add_invited_talk_teacher_flow.sql`

These migrations added course moderation fields/history, department-linked course resources, invited-talk resources, and invited-talk ownership/review fields.

## Backups Created

- Database backup: `/home/careeradmin/uet_ocw_before_f12a78e_20261125.sql.gz`
- Previous frontend backup: `/var/www/ocw-uet.before-f12a78e-20261125`
- Git stash label: `server-local-before-f12a78e`

Keep the Git stash until the deployment has been fully accepted. Inspect it with:

```bash
git -C /home/careeradmin/OCW-UET stash list
```

## Verification Results

The following checks passed after deployment:

- `ocw-uet-backend.service` reported `active`.
- `GET http://127.0.0.1:5202/api/health` returned:

```json
{
  "message": "UET Open Courseware API is running",
  "status": "success"
}
```

- The frontend root returned HTTP `200` through Nginx.

## Upload Limit Fix

After deployment, uploads larger than Nginx's default limit returned HTTP `413 Request Entity Too Large`. The active Nginx configuration was updated on 2026-11-25:

- Active configuration: `/etc/nginx/sites-available/ocw-uet`
- Enabled link: `/etc/nginx/sites-enabled/ocw-uet`
- Configuration backup: `/etc/nginx/sites-available/ocw-uet.before-upload-limit-20261125`
- The `5202` server block now contains `client_max_body_size 100m;`.
- `sudo nginx -t` passed and Nginx was reloaded successfully.
- This matches Flask's `MAX_CONTENT_LENGTH` value of 100 MB.

Verify the effective setting with:

```bash
sudo nginx -T 2>/dev/null | grep -n -A4 'listen 5202'
```

If the intended upload limit changes, update both Nginx and Flask so they remain aligned.

## Book Preview Performance

The frontend preview flow was optimized after large books were slow to open:

- Word documents retain retryable 2 MB range requests.
- After the first range determines total size, up to three later ranges download concurrently.
- Word previews show download percentage before browser-side document conversion.
- Other uploaded formats show streamed byte-download progress before the native preview opens.

Large Word files still require full browser-side conversion before their contents can be displayed. For unusually large or image-heavy documents, PDF is generally a faster preview format.

## Future Deployment Runbook

### 1. Inspect the repository

```bash
git -C /home/careeradmin/OCW-UET status --short --branch
git -C /home/careeradmin/OCW-UET log -1 --oneline
```

Preserve any server-local changes before pulling. Do not print `.env` file contents into chat or logs.

### 2. Back up the database

Use a new date or timestamp in the filename:

```bash
sudo mysqldump --single-transaction --routines --triggers uet_ocw | gzip > /home/careeradmin/uet_ocw_before_UPDATE_DATE.sql.gz
ls -lh /home/careeradmin/uet_ocw_before_UPDATE_DATE.sql.gz
```

### 3. Pull the code safely

```bash
git -C /home/careeradmin/OCW-UET pull --ff-only origin main
```

### 4. Review and apply new SQL migrations

Inspect new files under `uet-ocw-backend/sql/`. Apply only migrations that have not already been applied, and retain the database backup until verification is complete.

Example:

```bash
sudo mysql uet_ocw < /home/careeradmin/OCW-UET/uet-ocw-backend/sql/MIGRATION_FILE.sql
```

### 5. Update backend dependencies

```bash
/home/careeradmin/OCW-UET/uet-ocw-backend/venv/bin/python -m pip install -r /home/careeradmin/OCW-UET/uet-ocw-backend/requirements.txt
```

### 6. Build the frontend

```bash
cd /home/careeradmin/OCW-UET/uet-ocw-frontend
npm ci
npm run build
```

Do not run `npm audit fix` automatically during deployment because it can change locked dependency versions.

### 7. Back up and publish the frontend

Use a unique backup path for each deployment:

```bash
sudo cp -a /var/www/ocw-uet /var/www/ocw-uet.before-UPDATE_DATE
sudo rsync -a --delete /home/careeradmin/OCW-UET/uet-ocw-frontend/dist/ /var/www/ocw-uet/
```

### 8. Restart and verify

```bash
sudo systemctl restart ocw-uet-backend.service
sudo systemctl is-active ocw-uet-backend.service
curl -fsS http://127.0.0.1:5202/api/health && echo
curl -sS -o /dev/null -w "Frontend HTTP %{http_code}\n" http://127.0.0.1:5202/
```

Expected results are an active backend service, a successful API health response, and frontend HTTP `200`.

## Useful Diagnostic Commands

```bash
sudo ss -lntp | grep ':5202'
sudo systemctl status ocw-uet-backend.service --no-pager
sudo journalctl -u ocw-uet-backend.service -n 100 --no-pager
sudo nginx -T 2>/dev/null | grep -n -A20 -B5 'listen 5202'
sudo mysql -D uet_ocw -e "SHOW TABLES;"
```

## Security Notes

- Never commit or document SSH, sudo, MySQL, application, or test-account passwords.
- Do not commit `.env` files containing secrets.
- Verify the SSH host fingerprint through a trusted channel before accepting a new host key.
- Always create and verify a database backup before applying schema changes.
- Prefer `git pull --ff-only` so deployments do not create unexpected merge commits.
