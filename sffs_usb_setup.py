#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SFFS USB setup helper — list removable drives, optional copy, verify tree.

Usage:
    python sffs_usb_setup.py
    python sffs_usb_setup.py --verify
    python sffs_usb_setup.py --install   (pip install -r main-code/requirements.txt)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def list_removable() -> None:
    try:
        import psutil
    except ImportError:
        print("Install psutil to list drives: pip install psutil")
        return
    print("Partitions (look for removable / external):")
    for p in psutil.disk_partitions(all=False):
        print(f"  {p.device}  mount={p.mountpoint}  opts={p.opts}")


def verify() -> int:
    ok = True
    checks = [
        ("code1", ["f01_generate_key_pairs.py", "run_student1.py"]),
        ("code2", ["f07_create_isolated_sandbox.py", "run_student2.py"]),
        ("code3", ["f13_init_drive_detection.py", "run_student3.py"]),
        ("main-code", ["main.py", "sffs_core.py", "requirements.txt"]),
        ("tests", ["test_student1.py"]),
        ("docs", ["ARCHITECTURE.md"]),
    ]
    print("SFFS Installation Verification")
    print("================================")
    for folder, files in checks:
        d = ROOT / folder
        if not d.is_dir():
            print(f"FAIL: missing directory {folder}/")
            ok = False
            continue
        for f in files:
            if (d / f).is_file():
                print(f"OK: {folder}/{f}")
            else:
                print(f"FAIL: {folder}/{f}")
                ok = False
    for name in ("sffs.bat", "sffs.sh"):
        if (ROOT / name).is_file():
            print(f"OK: {name}")
        else:
            print(f"FAIL: {name}")
            ok = False

    # Import smoke
    sys.path[:0] = [str(ROOT / "code1"), str(ROOT / "code2"), str(ROOT / "code3"), str(ROOT / "main-code")]
    try:
        from f01_generate_key_pairs import generateKeyPairs  # noqa: F401
        print("OK: import Student 1")
        from f07_create_isolated_sandbox import createIsolatedSandbox  # noqa: F401
        print("OK: import Student 2")
        from f13_init_drive_detection import initDriveDetection  # noqa: F401
        print("OK: import Student 3")
        from sffs_core import SFFSCore  # noqa: F401
        print("OK: import SFFSCore")
    except Exception as e:
        print("FAIL: import check:", e)
        ok = False

    print()
    print("18 module files F01-F18 across code1/ code2/ code3/ (see docs/API_REFERENCE.md).")
    return 0 if ok else 1


def install_deps() -> int:
    req = ROOT / "main-code" / "requirements.txt"
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])
    except subprocess.CalledProcessError:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--install", action="store_true")
    args = ap.parse_args()

    if args.install:
        return install_deps()
    if args.verify:
        return verify()

    list_removable()
    print()
    print("Tip: python sffs_usb_setup.py --verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
