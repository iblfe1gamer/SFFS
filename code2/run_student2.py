"""
SFFS — Student 2 interactive demo runner.

Run from code2/ (imports use sibling modules). Demonstrates sandbox, memory wipe,
authentication, process checks, audit logging, and emergency lock (non-exit demo).
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import uuid
from pathlib import Path

_CODE2 = Path(__file__).resolve().parent
if str(_CODE2) not in sys.path:
    sys.path.insert(0, str(_CODE2))

from f07_create_isolated_sandbox import createIsolatedSandbox, destroySandbox
from f08_secure_memory_wipe import secureMemoryWipe
from f09_authenticate_user import (
    initAuthDatabase,
    registerUser,
    authenticateUser,
)
from f10_monitor_process import isDebuggerPresent, checkSuspiciousProcesses
from f11_write_audit_log import writeAuditLog, AuditLogger
from f12_emergency_lock import emergencyLock


def _menu() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="sffs_s2_"))
    db = tmp / "auth.db"
    initAuthDatabase(db)
    log_db = tmp / "audit.db"
    logger = AuditLogger(log_db)

    while True:
        print("\nSFFS - Student 2: System-Security Demo")
        print("=" * 42)
        print("[1] Create / destroy isolated sandbox")
        print("[2] Secure memory wipe (bytearray demo)")
        print("[3] Register user + authenticate (correct / wrong password)")
        print("[4] Debugger / suspicious process checks")
        print("[5] Write audit log entry (via AuditLogger)")
        print("[6] Emergency lock sandbox wipe (no sys.exit)")
        print("[0] Exit")
        choice = input("Select: ").strip()

        if choice == "0":
            shutil.rmtree(tmp, ignore_errors=True)
            break
        if choice == "1":
            sid = uuid.uuid4().hex[:8]
            base = tmp / "sandboxes"
            base.mkdir(parents=True, exist_ok=True)
            s = createIsolatedSandbox(base, session_id=sid)
            sp = Path(s["sandbox_path"])
            print("Created:", sp, sp.exists())
            destroySandbox(sp)
            print("Destroyed:", not sp.exists())
        elif choice == "2":
            buf = bytearray(b"secret!")
            secureMemoryWipe(buf)
            print("After wipe, all zero:", all(b == 0 for b in buf))
        elif choice == "3":
            u = input("Username [demo]: ").strip() or "demo"
            p1 = bytearray(input("Password: ").encode())
            try:
                registerUser(u, p1, db)
                print("Registered.")
            except Exception as e:
                print("Register:", e)
            p_ok = bytearray(input("Auth with password: ").encode())
            r = authenticateUser(u, p_ok, db)
            print("authenticateUser:", r)
            p_bad = bytearray(b"wrong_password_xyz")
            r2 = authenticateUser(u, p_bad, db)
            print("wrong pass:", r2)
        elif choice == "4":
            print("isDebuggerPresent:", isDebuggerPresent())
            print("checkSuspiciousProcesses:", checkSuspiciousProcesses())
        elif choice == "5":
            logger.log("Demo event from runner", "INFO", module="run_student2", user_id=None)
            print("Logged to", log_db)
        elif choice == "6":
            sid = uuid.uuid4().hex[:8]
            s = createIsolatedSandbox(tmp, session_id=sid)
            sp = Path(s["sandbox_path"])
            (sp / "x.txt").write_text("x")
            # emergencyLock may call sys.exit — patch for demo
            import f12_emergency_lock as el

            old_exit = el.sys.exit

            def _no_exit(_code=0):
                print("(demo: intercepted sys.exit)")

            el.sys.exit = _no_exit
            try:
                emergencyLock("MANUAL", sandbox_path=sp)
            finally:
                el.sys.exit = old_exit
            print("Sandbox exists after lock:", sp.exists())
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    _menu()
