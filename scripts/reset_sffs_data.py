#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reset SFFS local data for a clean test run.

  python reset_sffs_data.py --users        # remove auth.db (all accounts)
  python reset_sffs_data.py --keys       # remove RSA keystore + public key
  python reset_sffs_data.py --sandbox    # remove session sandboxes
  python reset_sffs_data.py --all -y       # users + keys + logs + sandboxes (keeps config)

Full wipe:

  python reset_sffs_data.py --full -y    # delete entire sffs_data/ under project USB root
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SFFS_DATA = ROOT / "sffs_data"


def _rm(path: Path) -> None:
    if path.is_file():
        path.unlink()
        print("Removed file:", path)
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
        print("Removed dir:", path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Reset SFFS local databases and keys")
    ap.add_argument("--users", action="store_true", help="Delete auth.db (registered users)")
    ap.add_argument("--keys", action="store_true", help="Delete keys/ (RSA + keystores)")
    ap.add_argument("--sandbox", action="store_true", help="Delete sandbox/ trees")
    ap.add_argument("--logs", action="store_true", help="Delete logs/ (audit DB)")
    ap.add_argument(
        "--all",
        action="store_true",
        help="Users + keys + sandbox + logs (not full sffs_data delete)",
    )
    ap.add_argument(
        "--full",
        action="store_true",
        help="Delete entire sffs_data/ directory",
    )
    ap.add_argument("-y", "--yes", action="store_true", help="Confirm destructive actions")
    args = ap.parse_args()

    if args.full:
        if not args.yes:
            print("Refusing: add -y to delete the whole folder:", SFFS_DATA)
            return 1
        if SFFS_DATA.exists():
            shutil.rmtree(SFFS_DATA)
            print("OK: removed", SFFS_DATA)
        else:
            print("Nothing to do:", SFFS_DATA, "missing")
        return 0

    if not any(
        [args.users, args.keys, args.sandbox, args.logs, args.all]
    ):
        ap.print_help()
        print("\nExample: python reset_sffs_data.py --all -y")
        return 1

    if not args.yes:
        print("Refusing: add -y to confirm")
        return 1

    do_users = args.users or args.all
    do_keys = args.keys or args.all
    do_sandbox = args.sandbox or args.all
    do_logs = args.logs or args.all

    if do_users:
        auth = SFFS_DATA / "auth.db"
        if auth.exists():
            auth.unlink()
            print("OK: removed", auth)
        else:
            print("(no auth.db)")

    if do_keys:
        kd = SFFS_DATA / "keys"
        if kd.exists():
            shutil.rmtree(kd)
            kd.mkdir(parents=True, exist_ok=True)
            print("OK: cleared", kd)
        else:
            print("(no keys/)")

    if do_sandbox:
        sd = SFFS_DATA / "sandbox"
        if sd.exists():
            shutil.rmtree(sd)
            sd.mkdir(parents=True, exist_ok=True)
            print("OK: cleared", sd)
        else:
            print("(no sandbox/)")

    if do_logs:
        ld = SFFS_DATA / "logs"
        if ld.exists():
            for f in ld.glob("*.db"):
                f.unlink()
                print("OK: removed", f)
        else:
            print("(no logs/)")

    print("Done. Register a new user in the app.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

