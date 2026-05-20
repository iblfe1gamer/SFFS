"""Student 3 — system architect module tests."""

import sys
import time
from pathlib import Path

import pytest

from f13_init_drive_detection import initDriveDetection
import f16_cloud_sync as cloud_mod
from f17_config_loader import configLoader
from f18_thread_controller import WorkerThread


def test_drive_detection_returns_valid_path() -> None:
    m = initDriveDetection()
    required = (
        "usb_root",
        "app_dir",
        "data_dir",
        "keys_dir",
        "sandbox_dir",
        "logs_dir",
        "config_dir",
        "backups_dir",
        "platform",
        "is_removable",
        "drive_label",
        "free_space_gb",
    )
    for k in required:
        assert k in m
    assert isinstance(m["usb_root"], Path)
    assert m["data_dir"].is_dir()


def test_config_save_and_load_roundtrip(tmp_path: Path) -> None:
    from Crypto.Random import get_random_bytes

    key = get_random_bytes(32)
    cfg_dir = tmp_path / "cfg"
    configLoader("save", cfg_dir, {"theme": "light"}, encryption_key=key)
    loaded = configLoader("load", cfg_dir, encryption_key=key)
    assert loaded["theme"] == "light"


def test_thread_controller_starts_without_blocking_main_thread() -> None:
    from PyQt6.QtCore import QCoreApplication

    def slow() -> str:
        time.sleep(0.5)
        return "done"

    app = QCoreApplication.instance() or QCoreApplication(sys.argv)
    t0 = time.perf_counter()
    worker = WorkerThread(slow, (), {})
    worker.start()
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.1
    worker.wait(3000)
    assert elapsed < 0.15


def test_cloud_sync_upload_contract_is_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "keys_backup.zip"
    src.write_bytes(b"encrypted-blob")
    cfg = tmp_path / "cfg"
    cfg.mkdir()

    captured: dict = {}

    class DummyMedia:
        def __init__(self, path, resumable=True):
            captured["media_path"] = path
            captured["media_resumable"] = resumable

    class DummyFilesApi:
        def create(self, body=None, media_body=None, fields=None):
            captured["create_body"] = body
            captured["create_fields"] = fields

            class _Exec:
                @staticmethod
                def execute():
                    return {"id": "file-123", "name": body["name"]}

            return _Exec()

        def list(self, q=None, spaces=None, fields=None):
            class _Exec:
                @staticmethod
                def execute():
                    return {"files": [{"id": "folder-1", "name": cloud_mod.BACKUP_FOLDER_NAME}]}

            return _Exec()

    class DummyService:
        def files(self):
            return DummyFilesApi()

    class DummyCreds:
        valid = True
        expired = False
        refresh_token = None

    monkeypatch.setattr(cloud_mod, "_GOOGLE_OK", True)
    monkeypatch.setattr(cloud_mod, "loadCredentials", lambda config_dir: DummyCreds())
    monkeypatch.setattr(cloud_mod, "build", lambda *args, **kwargs: DummyService(), raising=False)
    monkeypatch.setattr(cloud_mod, "MediaFileUpload", DummyMedia, raising=False)

    out = cloud_mod.cloudSync("upload", local_path=src, config_dir=cfg)
    assert out["status"] == "uploaded"
    assert captured["media_path"] == str(src)
    assert captured["media_resumable"] is True
    assert captured["create_body"]["name"] == f"sffs_{src.name}"
    assert captured["create_fields"] == "id,name"


def test_cloud_sync_upload_requires_real_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = tmp_path / "cfg"
    cfg.mkdir()

    class DummyCreds:
        valid = True
        expired = False
        refresh_token = None

    monkeypatch.setattr(cloud_mod, "_GOOGLE_OK", True)
    monkeypatch.setattr(cloud_mod, "loadCredentials", lambda config_dir: DummyCreds())
    monkeypatch.setattr(cloud_mod, "build", lambda *args, **kwargs: object(), raising=False)

    missing = tmp_path / "missing.zip"
    out = cloud_mod.cloudSync("upload", local_path=missing, config_dir=cfg)
    assert out["status"] == "error"
    assert "local_path must be a file" in out["message"]
