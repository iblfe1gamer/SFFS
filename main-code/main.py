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


def run_headless_demo() -> None:
    from getpass import getpass

    from f09_authenticate_user import initAuthDatabase, registerUser
    from sffs_core import SFFSCore

    core = SFFSCore()
    core.initialize()
    initAuthDatabase(core.paths["data_dir"] / "auth.db")

    print("=== SFFS headless demo ===")
    user = input("Username [demo_user]: ").strip() or "demo_user"
    mp = getpass("Account password (12+ chars, upper, lower, digit, special): ")

    db = core.paths["data_dir"] / "auth.db"
    reg = registerUser(user, bytearray(mp.encode()), db)
    if reg.get("status") == "registered":
        print("Registered new user.")
    else:
        print("Register:", reg.get("message", reg))

    pw = bytearray(getpass("Login password (same as account): ").encode())
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
    from PyQt6.QtCore import QEvent, QObject
    from PyQt6.QtWidgets import (
        QApplication,
        QDialog,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
    )

    from f09_authenticate_user import registerUser
    from f14_ui_dashboard import SFSSDashboard, apply_sffs_theme
    from mouse_entropy import feed_mouse_entropy
    from sffs_core import SFFSCore

    class _EntropyFilter(QObject):
        def eventFilter(self, obj, event):  # noqa: ANN001
            if event.type() == QEvent.Type.MouseMove:
                feed_mouse_entropy(event.pos().x(), event.pos().y())
            return False

    core = SFFSCore()
    core.initialize()

    app = QApplication.instance() or QApplication(sys.argv)
    apply_sffs_theme(app)
    app.installEventFilter(_EntropyFilter(app))

    login = QDialog()
    login.setWindowTitle("SFFS - Login or Register")
    root = QVBoxLayout(login)
    root.addWidget(
        QLabel(
            "Password policy: at least 12 characters with uppercase, lowercase, "
            "a digit, and a special character (!@#$...)."
        )
    )
    form = QFormLayout()
    u = QLineEdit()
    u.setText("demo_user")
    p = QLineEdit()
    p.setEchoMode(QLineEdit.EchoMode.Password)
    p.setPlaceholderText("Your password unlocks keys and files for this session")
    form.addRow("Username", u)
    form.addRow("Password", p)
    root.addLayout(form)

    btn_row = QHBoxLayout()
    btn_reg = QPushButton("Register")
    btn_log = QPushButton("Log in")
    btn_quit = QPushButton("Quit")
    btn_row.addWidget(btn_reg)
    btn_row.addWidget(btn_log)
    btn_row.addWidget(btn_quit)
    root.addLayout(btn_row)

    db_path = core.paths["data_dir"] / "auth.db"

    def do_register() -> None:
        name = u.text().strip()
        if not name:
            QMessageBox.warning(login, "SFFS", "Enter a username.")
            return
        res = registerUser(name, bytearray(p.text().encode()), db_path)
        if res.get("status") == "registered":
            QMessageBox.information(
                login,
                "SFFS",
                "Account created. Click Log in with the same password.",
            )
        else:
            QMessageBox.warning(
                login,
                "Register failed",
                res.get("message", str(res)),
            )

    def do_login_click() -> None:
        name = u.text().strip()
        if not name:
            QMessageBox.warning(login, "SFFS", "Enter a username.")
            return
        r = core.login(name, bytearray(p.text().encode()))
        if r.get("authenticated"):
            login.accept()
        else:
            QMessageBox.warning(
                login,
                "Login failed",
                r.get("message", "Invalid username or password."),
            )

    btn_reg.clicked.connect(do_register)
    btn_log.clicked.connect(do_login_click)
    btn_quit.clicked.connect(login.reject)

    if login.exec() != int(QDialog.DialogCode.Accepted):
        return 0

    def handle_logout() -> None:
        core.logout()
        app.quit()

    win = SFSSDashboard(
        core.session_token or "",
        core.config or {},
        core.paths or {},
        core=core,
        on_logout=handle_logout,
    )
    win.setWindowTitle("SFFS")

    def do_encrypt() -> None:
        fp = win._selected_file
        if not fp:
            QMessageBox.information(win, "SFFS", "Select a file via drag-and-drop first.")
            return
        try:
            out = core.encryptFileOperation(Path(fp))
            win._status.setText(f"Encrypted: {out['sffs_path'].name}")
            win.refresh_sandbox_list()
        except Exception as e:
            QMessageBox.warning(win, "Encrypt failed", str(e))

    def do_decrypt() -> None:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(win, "Open .sffs", "", "SFFS (*.sffs)")
        if not path:
            return
        try:
            out = core.decryptFileOperation(Path(path))
            win._status.setText(f"Decrypted to sandbox: {out['output_path'].name}")
            win.refresh_sandbox_list()
        except Exception as e:
            QMessageBox.warning(win, "Decrypt failed", str(e))

    win._enc.clicked.connect(do_encrypt)
    win._dec.clicked.connect(do_decrypt)
    win.refresh_sandbox_list()
    win.show()
    rc = app.exec()
    if core.session_token:
        core.logout()
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
        run_headless_demo()
        return 0
    return run_full_app()


if __name__ == "__main__":
    raise SystemExit(main())
