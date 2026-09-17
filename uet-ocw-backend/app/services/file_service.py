import io
import json
import os
import re
from pathlib import Path

from werkzeug.utils import secure_filename


def normalize_folder_path(folder_name):
    if folder_name is None:
        return ""

    cleaned = str(folder_name).replace("\\", "/").strip("/")
    parts = []
    for part in cleaned.split("/"):
        part = part.strip()
        if not part and part != ".":
            continue
        safe = re.sub(r"[^A-Za-z0-9._-]", "-", part)
        safe = safe.strip(".-")
        if safe:
            parts.append(safe)
    return "/".join(parts)


def ensure_unique_path(target_dir, filename):
    candidate = target_dir / filename
    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_candidate = target_dir / new_name
        if not new_candidate.exists():
            return new_candidate
        counter += 1


def save_uploaded_file(file_storage, folder="", upload_root=None):
    if file_storage is None or not getattr(file_storage, "filename", None):
        raise ValueError("No file selected for upload")

    base_dir = Path(upload_root) if upload_root else Path(os.getenv("UPLOAD_FOLDER", str(Path(__file__).resolve().parents[2] / "uploads")))
    directory = base_dir / normalize_folder_path(folder)
    directory.mkdir(parents=True, exist_ok=True)

    original_name = secure_filename(file_storage.filename)
    if not original_name:
        original_name = f"upload_{int(__import__('time').time())}.bin"

    final_path = ensure_unique_path(directory, original_name)
    file_storage.save(str(final_path))

    relative_path = final_path.relative_to(base_dir)
    local_url = "/uploads/" + relative_path.as_posix()

    drive_url = None
    drive_file_id = None
    drive_error = None
    try:
        drive_url, drive_file_id = upload_to_google_drive(final_path, folder)
    except Exception as exc:
        drive_error = str(exc)
        drive_url = None
        drive_file_id = None

    return {
        "filename": final_path.name,
        "stored_name": final_path.name,
        "local_path": str(final_path),
        "relative_path": relative_path.as_posix(),
        "local_url": local_url,
        "folder": normalize_folder_path(folder),
        "size": final_path.stat().st_size,
        "mime_type": file_storage.mimetype or "application/octet-stream",
        "drive_file_id": drive_file_id,
        "drive_url": drive_url,
        "drive_error": drive_error,
        "drive_uploaded": bool(drive_url or drive_file_id),
    }


def _google_drive_credentials():
    from google.oauth2 import service_account

    credentials_json = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_DRIVE_CREDENTIALS_JSON")
    credentials_path = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH") or os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")

    if credentials_json:
        try:
            if os.path.exists(credentials_json):
                with open(credentials_json, "r", encoding="utf-8") as file:
                    credentials_json = file.read()
            return service_account.Credentials.from_service_account_info(
                json.loads(credentials_json),
                scopes=["https://www.googleapis.com/auth/drive"],
            )
        except Exception:
            return None

    if credentials_path and os.path.exists(credentials_path):
        try:
            return service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/drive"],
            )
        except Exception:
            return None

    return None


def _find_or_create_drive_folder(service, parent_id, folder_name):
    folder_name = str(folder_name).strip()
    if not folder_name:
        return parent_id

    query = "mimeType='application/vnd.google-apps.folder' and name = '{}' and trashed = false".format(folder_name.replace("'", "\\'"))
    if parent_id:
        query = query + " and '{}' in parents".format(parent_id)

    response = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name)",
        pageSize=10,
    ).execute()

    folders = response.get("files", [])
    if folders:
        return folders[0]["id"]

    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        file_metadata["parents"] = [parent_id]

    created = service.files().create(
        body=file_metadata,
        fields="id",
    ).execute()
    return created.get("id")


def upload_to_google_drive(local_file_path, folder_name=""):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload

    credentials = _google_drive_credentials()
    if credentials is None:
        return None, None

    root_folder_name = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_NAME", "OCW")
    root_parent_id = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER_ID")

    service = build("drive", "v3", credentials=credentials)
    current_parent_id = root_parent_id

    if current_parent_id is None:
        current_parent_id = _find_or_create_drive_folder(service, None, root_folder_name)
    else:
        current_parent_id = _find_or_create_drive_folder(service, root_parent_id, root_folder_name) if root_folder_name and root_folder_name != "" else root_parent_id

    safe_folder = normalize_folder_path(folder_name)
    if safe_folder:
        for path_part in safe_folder.split("/"):
            current_parent_id = _find_or_create_drive_folder(service, current_parent_id, path_part)

    file_name = Path(local_file_path).name
    file_metadata = {
        "name": file_name,
        "parents": [current_parent_id],
    }

    with open(local_file_path, "rb") as file_handle:
        media = MediaIoBaseUpload(
            io.BytesIO(file_handle.read()),
            mimetype="application/octet-stream",
            resumable=True,
        )
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,webViewLink,webContentLink",
        ).execute()

    if file.get("webViewLink"):
        return file["webViewLink"], file.get("id")
    if file.get("webContentLink"):
        return file["webContentLink"], file.get("id")
    return None, file.get("id")
