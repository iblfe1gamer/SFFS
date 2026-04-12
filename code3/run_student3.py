"""
Interactive demo runner for Student 3 (System Architect) modules.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_CODE3 = Path(__file__).resolve().parent
_ROOT = _CODE3.parent
for p in (_CODE3, _ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _opt1() -> None:
    from f13_init_drive_detection import initDriveDetection, getAvailableSpace

    m = initDriveDetection()
    for k, v in m.items():
        print(f"  {k}: {v}")
    print("  space:", getAvailableSpace(m["usb_root"]))


def _opt2() -> None:
    from f17_config_loader import configLoader, validateConfig
    from Crypto.Random import get_random_bytes

    cfg_dir = _CODE3 / "test_output" / "runner_config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    key = get_random_bytes(32)
    configLoader("save", cfg_dir, {"theme": "light", "ui_show_advanced": True}, encryption_key=key)
    loaded = configLoader("load", cfg_dir, encryption_key=key)
    print("Loaded:", loaded.get("theme"), validateConfig(loaded))


def _opt3() -> None:
    from f14_ui_dashboard import uiDashboard

    paths = {"data_dir": _ROOT / "sffs_data", "free_space_gb": 0.0}
    paths["data_dir"].mkdir(parents=True, exist_ok=True)
    uiDashboard("demo-token", {}, paths)


def _opt4() -> None:
    from f15_file_manager_explorer import fileManagerExplorer
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    w = fileManagerExplorer(Path.cwd(), None)
    w.setWindowTitle("SFFS Explorer")
    w.resize(880, 520)
    w.show()
    app.exec()


def _opt5() -> None:
    from PyQt6.QtCore import QCoreApplication
    from f18_thread_controller import WorkerThread

    def task() -> str:
        for _ in range(6):
            time.sleep(0.2)
        return "worker_ok"

    app = QCoreApplication(sys.argv)
    out: list = []
    worker = WorkerThread(task, (), {})
    worker.signals.result.connect(out.append)
    worker.signals.error.connect(out.append)
    worker.signals.finished.connect(app.quit)
    worker.start()
    app.exec()
    print("Thread result:", out)


def _opt6() -> None:
    from f16_cloud_sync import cloudSync

    cfg = _CODE3 / "test_output" / "cloud_cfg"
    cfg.mkdir(parents=True, exist_ok=True)
    print(cloudSync("list", config_dir=cfg))


def _opt7() -> None:
    from PyQt6.QtCore import QCoreApplication
    from f13_init_drive_detection import initDriveDetection
    from f17_config_loader import configLoader
    from f18_thread_controller import WorkerThread
    from Crypto.Random import get_random_bytes

    checks = []

    paths = initDriveDetection()
    need = (
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
    checks.append(("path_map_keys", all(k in paths for k in need)))

    key = get_random_bytes(32)
    cd = paths["config_dir"] / "integration_test"
    cd.mkdir(parents=True, exist_ok=True)
    configLoader("save", cd, {"theme": "dark"}, encryption_key=key)
    ld = configLoader("load", cd, encryption_key=key)
    checks.append(("config_roundtrip", ld.get("theme") == "dark"))

    app = QCoreApplication(sys.argv)
    box: list = []

    def job() -> str:
        time.sleep(0.15)
        return "thread_ok"

    worker = WorkerThread(job, (), {})
    worker.signals.result.connect(lambda r: box.append(r))
    worker.signals.finished.connect(app.quit)
    worker.start()
    app.exec()
    checks.append(("thread", box == ["thread_ok"]))

    for name, ok in checks:
        print(f"  [{name}]: {'PASS' if ok else 'FAIL'}")
    print("OVERALL:", "PASS" if all(c[1] for c in checks) else "FAIL")


def main() -> None:
    while True:
        print("\nSFFS - Student 3: System Architect Demo")
        print("=" * 42)
        print("[1] Detect USB drive and show path map")
        print("[2] Load / save configuration")
        print("[3] Launch UI dashboard (requires display)")
        print("[4] Open file manager explorer (requires display)")
        print("[5] Test thread controller (background task)")
        print("[6] Test cloud sync (requires Google credentials)")
        print("[7] Full integration test (headless-safe)")
        print("[0] Exit")
        c = input("Select: ").strip()
        if c == "0":
            break
        try:
            if c == "1":
                _opt1()
            elif c == "2":
                _opt2()
            elif c == "3":
                _opt3()
            elif c == "4":
                _opt4()
            elif c == "5":
                _opt5()
            elif c == "6":
                _opt6()
            elif c == "7":
                _opt7()
            else:
                print("Invalid choice.")
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
