"""
os_isolation.py - OS-level isolation detection and policy gate.

Owned by Student 2 (runtime/system security).
"""

from __future__ import annotations

import os
import platform
from pathlib import Path


def _linux_apparmor_confined() -> tuple[bool, str]:
    marker = os.environ.get("SFFS_OS_ISOLATION", "")
    if marker != "apparmor":
        return False, "launcher did not mark AppArmor mode"
    current = Path("/proc/self/attr/current")
    if not current.exists():
        return False, "AppArmor attribute file missing"
    value = current.read_text(encoding="utf-8", errors="ignore").strip()
    if value.startswith("unconfined"):
        return False, "process is unconfined"
    return True, f"confined profile: {value}"


def _windows_job_confined() -> tuple[bool, str]:
    marker = os.environ.get("SFFS_OS_ISOLATION", "")
    if marker != "windows_job":
        return False, "launcher did not mark Windows Job mode"
    if os.environ.get("SFFS_JOB_OBJECT_ACTIVE") != "1":
        return False, "job object wrapper marker missing"
    return True, "job object marker active"


def detect_isolation() -> dict:
    system = platform.system().lower()
    if system == "linux":
        ok, reason = _linux_apparmor_confined()
        return {"platform": "linux", "active": ok, "mode": "apparmor", "reason": reason}
    if system == "windows":
        ok, reason = _windows_job_confined()
        return {"platform": "windows", "active": ok, "mode": "windows_job", "reason": reason}
    return {"platform": system, "active": False, "mode": "unsupported", "reason": "unsupported platform"}


def ensure_secure_mode() -> None:
    status = detect_isolation()
    if not status["active"]:
        raise RuntimeError(
            f"Secure mode requires OS isolation. platform={status['platform']} "
            f"mode={status['mode']} reason={status['reason']}"
        )
