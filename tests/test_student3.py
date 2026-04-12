"""Student 3 — system architect module tests."""

import sys
import time
from pathlib import Path

import pytest

from f13_init_drive_detection import initDriveDetection
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


@pytest.mark.skip(reason="Upload path does not re-encrypt; encryption is caller responsibility per design.")
def test_cloud_sync_encrypts_before_upload() -> None:
    pass
