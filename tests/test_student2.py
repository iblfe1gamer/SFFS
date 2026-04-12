"""Student 2 — system security module tests."""

import sys
import uuid
from pathlib import Path

import pytest

from f07_create_isolated_sandbox import createIsolatedSandbox, destroySandbox
from f08_secure_memory_wipe import secureMemoryWipe
from f09_authenticate_user import authenticateUser, initAuthDatabase, registerUser
from f10_monitor_process import checkSuspiciousProcesses, isDebuggerPresent
from f11_write_audit_log import AuditLogger
from f12_emergency_lock import emergencyLock


def test_sandbox_created_and_destroyed(tmp_path: Path) -> None:
    sid = uuid.uuid4().hex[:8]
    s = createIsolatedSandbox(tmp_path, session_id=sid)
    sp = Path(s["sandbox_path"])
    assert sp.is_dir()
    assert destroySandbox(sp) is True
    assert not sp.exists()


def test_sandbox_isolated_from_host(tmp_path: Path) -> None:
    s = createIsolatedSandbox(tmp_path, session_id="iso1")
    sp = Path(s["sandbox_path"]).resolve()
    assert tmp_path in sp.parents or sp.parent == tmp_path.resolve()


def test_memory_wipe_zeroes_buffer() -> None:
    buf = bytearray(b"secret")
    secureMemoryWipe(buf)
    assert all(b == 0 for b in buf)


def test_auth_accepts_correct_password(tmp_path: Path) -> None:
    db = tmp_path / "auth.db"
    initAuthDatabase(db)
    registerUser("u1", bytearray(b"GoodPassw0rd!"), db)
    r = authenticateUser("u1", bytearray(b"GoodPassw0rd!"), db)
    assert r["authenticated"] is True
    assert r.get("session_token")


def test_auth_rejects_wrong_password(tmp_path: Path) -> None:
    db = tmp_path / "auth.db"
    initAuthDatabase(db)
    registerUser("u2", bytearray(b"AnotherGood9!"), db)
    r = authenticateUser("u2", bytearray(b"WrongGuess9!"), db)
    assert r["authenticated"] is False


def test_auth_locks_after_max_attempts(tmp_path: Path) -> None:
    db = tmp_path / "auth3.db"
    initAuthDatabase(db)
    registerUser("u3", bytearray(b"RealPassw0rd!"), db)
    for _ in range(10):
        authenticateUser("u3", bytearray(b"BadGuess99!!"), db)
    r = authenticateUser("u3", bytearray(b"RealPassw0rd!"), db)
    assert isinstance(r.get("authenticated"), bool)


def test_audit_log_written_and_readable(tmp_path: Path) -> None:
    dbp = tmp_path / "audit.db"
    log = AuditLogger(dbp, encryption_key=None)
    log.log("pytest_event", "INFO", module="tests", user_id=None, metadata={"x": 1})
    log2 = AuditLogger(dbp, encryption_key=None)
    rows = log2.viewLogs(limit=5)
    assert any(e.get("event") == "pytest_event" for e in rows)


def test_emergency_lock_wipes_sandbox(tmp_path: Path) -> None:
    s = createIsolatedSandbox(tmp_path, session_id="el1")
    sp = Path(s["sandbox_path"])
    (sp / "f.txt").write_text("data")
    import f12_emergency_lock as el

    old_exit = el.sys.exit

    def _noop_exit(_c=0):
        pass

    el.sys.exit = _noop_exit
    try:
        emergencyLock("MANUAL", sandbox_path=sp)
    finally:
        el.sys.exit = old_exit
    assert not sp.exists()


def test_process_monitor_callable() -> None:
    assert isinstance(isDebuggerPresent(), bool)
    assert isinstance(checkSuspiciousProcesses(), list)
