# Production deployment files

The current production layout is:

- Nginx serves the React build on public port `5205`.
- Gunicorn serves Flask privately on `127.0.0.1:5206`.
- Nginx proxies `/api`, `/uploads`, `/admin`, `/moderator`, `/apidocs`, and
  `/openapi.json` to Flask.
- Nginx accepts request bodies up to `100m`, matching Flask's 100 MB upload
  limit. Requests larger than that receive HTTP 413.
- `UPLOAD_FOLDER=uploads` is portable. The backend resolves it from the
  `uet-ocw-backend` directory; an absolute production path is also supported.

Install the service file at `/etc/systemd/system/uet-ocw-backend.service` and
include `nginx-uet-ocw.conf` in the Nginx server listening on port `5205`.

After deploying an update:

```bash
systemctl daemon-reload
systemctl restart uet-ocw-backend
nginx -t && systemctl reload nginx
```
