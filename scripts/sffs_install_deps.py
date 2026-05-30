#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install missing SFFS dependencies from main-code/requirements.txt (cross-platform)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQ = ROOT / "main-code" / "requirements.txt"

# Map pip package name -> import name to test
PKG_IMPORTS = [
    ("cryptography", "cryptography"),
    ("pycryptodome", "Crypto"),
    ("argon2-cffi", "argon2"),
    ("psutil", "psutil"),
    ("PyQt6", "PyQt6"),
    ("google-api-python-client", "googleapiclient"),
    ("google-auth-oauthlib", "google_auth_oauthlib"),
    ("google-auth-httplib2", "google_auth_httplib2"),
]


def main() -> int:
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10+ required.")
        return 1
    if not REQ.is_file():
        print("ERROR: Missing", REQ)
        return 1

    missing_pip: list[str] = []
    for pip_name, imp in PKG_IMPORTS:
        if importlib.util.find_spec(imp.split(".")[0]) is None:
            missing_pip.append(pip_name)

    if not missing_pip:
        print("All tracked dependencies appear importable.")
        return 0

    print("Missing or not importable:", ", ".join(missing_pip))
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQ)],
        )
    except subprocess.CalledProcessError:
        print("pip install failed. Install pip and retry.")
        return 1
    print("OK: dependencies installed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

