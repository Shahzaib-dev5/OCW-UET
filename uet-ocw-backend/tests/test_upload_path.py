from pathlib import Path

from app import _resolve_upload_root


def test_relative_upload_folder_resolves_from_backend_root(monkeypatch):
    monkeypatch.setenv("UPLOAD_FOLDER", "uploads")

    expected = Path(__file__).resolve().parents[1] / "uploads"

    assert _resolve_upload_root() == expected.resolve()


def test_absolute_upload_folder_is_preserved(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path))

    assert _resolve_upload_root() == tmp_path.resolve()
