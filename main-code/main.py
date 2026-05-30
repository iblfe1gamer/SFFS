#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — SFFS Entry Point

    python main.py                 # GUI (login + dashboard)
    python main.py --headless      # CLI demo pipeline
    python main.py --student 1     # Student 1 runner
    python main.py --test          # pytest tests/
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Repository root (parent of main-code/)
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "code1", _ROOT / "code2", _ROOT / "code3", _ROOT / "main-code"):
    s = str(_p)
    if s not in sys.path:
        sys.path.insert(0, s)
from os_isolation import detect_isolation, ensure_secure_mode


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SFFS - Smart File Fortify System")
    p.add_argument("--headless", action="store_true", help="CLI demo (no GUI)")
    p.add_argument("--student", type=int, choices=(1, 2, 3), help="Run student demo runner")
    p.add_argument("--test", action="store_true", help="Run pytest suite")
    p.add_argument(
        "--secure-required",
        action="store_true",
        help="Require OS-level isolation markers before starting",
    )
    p.add_argument(
        "--usb-root",
        type=Path,
        default=None,
        help="Override USB root (advanced)",
    )
    p.add_argument("--demo-user",     default="demo_user", help="Headless demo username")
    p.add_argument("--demo-password", default=None,        help="Headless demo password (skips prompt)")
    return p.parse_args()


def run_tests() -> int:
    exe = sys.executable
    r = subprocess.run([exe, "-m", "pytest", str(_ROOT / "tests"), "-v"], cwd=str(_ROOT))
    return r.returncode


def run_student_demo(n: int) -> int:
    exe = sys.executable
    script = _ROOT / f"code{n}" / f"run_student{n}.py"
    r = subprocess.run([exe, str(script)], cwd=str(_ROOT))
    return r.returncode


def run_headless_demo(args) -> None:
    from getpass import getpass

    from f09_authenticate_user import initAuthDatabase, registerUser
    from sffs_core import SFFSCore

    _DEMO_PASSWORD = "Demo@SFFS2025!"  # meets policy: 12+, upper, lower, digit, special

    interactive = sys.stdin.isatty()

    core = SFFSCore()
    core.initialize()
    initAuthDatabase(core.paths["data_dir"] / "auth.db")

    print("=== SFFS headless demo ===")

    if interactive and not args.demo_password:
        user = input("Username [demo_user]: ").strip() or "demo_user"
        mp   = getpass("Account password (12+ chars, upper, lower, digit, special): ")
    else:
        user = args.demo_user
        mp   = args.demo_password or _DEMO_PASSWORD
        print(f"Non-interactive — using demo credentials for user '{user}'")

    db  = core.paths["data_dir"] / "auth.db"
    reg = registerUser(user, bytearray(mp.encode()), db)
    if reg.get("status") == "registered":
        print("Registered new user.")
    else:
        print("Register:", reg.get("message", reg))

    pw = bytearray((args.demo_password or mp).encode()) if (not interactive or args.demo_password) \
        else bytearray(getpass("Login password (same as account): ").encode())
    auth = core.login(user, pw)
    if not auth.get("authenticated"):
        print("Login failed:", auth)
        return

    td = core.paths["data_dir"] / "headless_demo.txt"
    td.write_text("SFFS headless test payload.\n", encoding="utf-8")
    print("Encrypting:", td)
    enc = core.encryptFileOperation(td)
    print(" ->", enc["sffs_path"])
    print("Decrypting...")
    dec = core.decryptFileOperation(enc["sffs_path"])
    print(" ->", dec["output_path"], dec.get("integrity"))
    core.logout()
    print("Done.")


def run_full_app() -> int:
    """Launch SFFS with the modern UI (sffs_ui.py)."""
    from PyQt6.QtWidgets import QApplication, QDialog
    from sffs_ui import LoginWindow, SFFSWindow, apply_theme
    from sffs_core import SFFSCore
    from os_isolation import detect_isolation

    # Auto-activate Windows Job Object isolation when not launched via sffs.bat.
    # On Linux this is a no-op; on Windows it creates the Job Object and sets
    # the env markers that detect_isolation() checks.
    if _ROOT not in sys.path:
        sys.path.insert(0, str(_ROOT / "code2"))
    try:
        from windows_job_wrapper import try_activate_job_for_current_process
        try_activate_job_for_current_process()
    except Exception:
        pass  # Non-Windows or ctypes unavailable — isolation badge will show warn

    core = SFFSCore()
    core.initialize()

    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app)

    # ── Login ──────────────────────────────────────────────────────────────
    login = LoginWindow(core.paths or {}, core=core)
    if login.exec() != int(QDialog.DialogCode.Accepted) or not login.session_token:
        return 0

    # ── Main window ────────────────────────────────────────────────────────
    def handle_logout() -> None:
        try:
            core.logout()
        except Exception:
            pass
        app.quit()

    win = SFFSWindow(
        session_token=core.session_token or "",
        config=core.config or {},
        paths=core.paths or {},
        core=core,
        username=login.username,
        on_logout=handle_logout,
    )

    # Live security badge
    iso = detect_isolation()
    if iso.get("active"):
        win.set_security_status("● SECURE", "secure")
    else:
        win.set_security_status("⚠ NO ISOLATION", "warn")

    # Wire core threat/USB callbacks → UI alerts
    core.set_gui_alert_callback(win.showSecurityAlert)

    win.show()
    rc = app.exec()
    try:
        if core.session_token:
            core.logout()
    except Exception:
        pass
    return rc


def main() -> int:
    args = parse_args()
    if args.secure_required:
        ensure_secure_mode()
    status = detect_isolation()
    if status.get("active"):
        print(f"[SFFS] OS isolation active: {status['mode']} ({status['reason']})")
    elif args.secure_required:
        # ensure_secure_mode already raised; this is defensive.
        return 1
    if args.test:
        return run_tests()
    if args.student:
        return run_student_demo(args.student)
    if args.headless:
        run_headless_demo(args)
        return 0
    return run_full_app()


if __name__ == "__main__":
    raise SystemExit(main())
