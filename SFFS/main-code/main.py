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
import os
import subprocess
import sys
from pathlib import Path

# Repository root — overridden by SFFS_ROOT env var when launched from USB
_env_root = os.environ.get("SFFS_ROOT")
if _env_root:
    _ROOT = Path(_env_root)
else:
    _ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "code1", _ROOT / "code2", _ROOT / "code3", _ROOT / "main-code"):
    s = str(_p)
    if s not in sys.path:
        sys.path.insert(0, s)
_usb_root: "Path | None" = _ROOT if _env_root else None
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
    core.initialize(root_path=_usb_root)
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
    from PyQt6.QtCore import QEvent, QObject, Qt, QTimer
    from PyQt6.QtWidgets import (
        QApplication,
        QDialog,
        QFileDialog,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QProgressBar,
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
    core.initialize(root_path=_usb_root)

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

    _entropy_state = {"mode": "silent"}

    def show_entropy_dialog() -> bool:
        from mouse_entropy import get_entropy_pool_status
        dlg = QDialog(win)
        dlg.setWindowTitle("Collecting Entropy")
        dlg.setModal(True)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(
            "Move your mouse randomly over this window\n"
            "to generate encryption entropy."
        ))
        bar = QProgressBar()
        bar.setRange(0, 100)
        lay.addWidget(bar)
        status_label = QLabel("0%")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(status_label)
        timer = QTimer()

        def _update() -> None:
            s = get_entropy_pool_status()
            bar.setValue(s["percentage"])
            status_label.setText(f"{s['percentage']}%")
            if s["is_ready"]:
                timer.stop()
                dlg.accept()

        timer.timeout.connect(_update)
        timer.start(100)
        result = dlg.exec()
        timer.stop()
        return result == int(QDialog.DialogCode.Accepted)

    def do_encrypt() -> None:
        fp = win._selected_file
        if not fp:
            QMessageBox.information(win, "SFFS", "Select a file via drag-and-drop first.")
            return
        if _entropy_state["mode"] == "interactive":
            if not show_entropy_dialog():
                return
        try:
            out = core.encryptFileOperation(Path(fp))
            win._status.setText(f"Encrypted: {out['sffs_path'].name}")
            win.refresh_sandbox_list()
        except RuntimeError as e:
            if "INSUFFICIENT_ENTROPY" in str(e):
                QMessageBox.warning(
                    win,
                    "Entropy Required",
                    "Please move your mouse randomly over the window before encrypting.",
                )
            else:
                QMessageBox.warning(win, "Encrypt failed", str(e))
        except Exception as e:
            QMessageBox.warning(win, "Encrypt failed", str(e))

    def do_decrypt() -> None:
        path, _ = QFileDialog.getOpenFileName(win, "Open .sffs", "", "SFFS (*.sffs)")
        if not path:
            return

        msg = QMessageBox(win)
        msg.setWindowTitle("Decrypt Location")
        msg.setText(
            "Where should the decrypted file be saved?\n\n"
            "  Sandbox — Temporary, auto-wiped on logout\n"
            "  Disk — Permanent, stays until you delete it"
        )
        sandbox_btn = msg.addButton("Sandbox", QMessageBox.ButtonRole.AcceptRole)
        disk_btn = msg.addButton("Disk…", QMessageBox.ButtonRole.ActionRole)
        msg.addButton(QMessageBox.StandardButton.Cancel)
        msg.setDefaultButton(sandbox_btn)
        msg.exec()
        clicked = msg.clickedButton()

        if clicked == disk_btn:
            warn = QMessageBox.warning(
                win,
                "Security Warning",
                "This file will be decrypted to your chosen location on disk.\n"
                "It will NOT be placed in the sandbox and will NOT be\n"
                "automatically wiped when you end your session.\n\n"
                "The decrypted file will remain on disk until you delete it.",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if warn == QMessageBox.StandardButton.Cancel:
                return
            save_path, _ = QFileDialog.getSaveFileName(
                win,
                "Save Decrypted File",
                Path(path).stem,
            )
            if not save_path:
                return
            try:
                out = core.decryptFileOperation(Path(path), output_path=Path(save_path))
                win._status.setText(f"Decrypted to: {out['output_path']}")
            except Exception as e:
                QMessageBox.warning(win, "Decrypt failed", str(e))
        elif clicked == sandbox_btn:
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
    global _usb_root
    args = parse_args()
    if args.usb_root:
        _usb_root = args.usb_root
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
