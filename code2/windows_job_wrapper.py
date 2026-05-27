#!/usr/bin/env python3
"""
windows_job_wrapper.py - Launch SFFS in a constrained Windows Job Object.

Owned by Student 2 (runtime/system security).
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# Pseudo-handle for the current process (AssignProcessToJobObject accepts this).
_CURRENT_PROCESS_PSEUDO = ctypes.c_void_p(-1)

kernel32.AssignProcessToJobObject.argtypes = (ctypes.c_void_p, ctypes.c_void_p)
kernel32.AssignProcessToJobObject.restype = wintypes.BOOL

JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
JobObjectExtendedLimitInformation = 9
PROCESS_SET_QUOTA = 0x0100
PROCESS_TERMINATE = 0x0001


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def _check_bool(ok: int, msg: str) -> None:
    if not ok:
        err = ctypes.get_last_error()
        raise OSError(err, f"{msg} (winerr={err})")


def _create_job_object() -> int:
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    hjob = kernel32.CreateJobObjectW(None, "SFFSJobObject")
    _check_bool(hjob, "CreateJobObjectW failed")

    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = (
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_ACTIVE_PROCESS
    )
    info.BasicLimitInformation.ActiveProcessLimit = 8

    _check_bool(
        kernel32.SetInformationJobObject(
            hjob,
            JobObjectExtendedLimitInformation,
            ctypes.byref(info),
            ctypes.sizeof(info),
        ),
        "SetInformationJobObject failed",
    )
    return hjob


def _assign_process_to_job(hjob: int, pid: int) -> None:
    kernel32.OpenProcess.restype = wintypes.HANDLE
    hproc = kernel32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, pid)
    _check_bool(hproc, "OpenProcess failed")
    try:
        _check_bool(
            kernel32.AssignProcessToJobObject(ctypes.c_void_p(hjob), ctypes.c_void_p(hproc)),
            "AssignProcessToJobObject failed",
        )
    finally:
        kernel32.CloseHandle(hproc)


# Keep the job object alive for the lifetime of this process (closing the last handle
# can tear down the job if no other references exist).
_SFFS_JOB_HANDLE: int | None = None


def try_activate_job_for_current_process() -> bool:
    """
    If this process is not already marked as job-isolated, create a Windows Job Object,
    assign the current process to it, and set SFFS_OS_ISOLATION / SFFS_JOB_OBJECT_ACTIVE.

    Used when SFFS was started without sffs.bat (e.g. python main-code/main.py) but
    secure external launch is still required. When started via sffs.bat, env markers
    are already set and this becomes a no-op.

    Returns True if env markers are now set so detect_isolation() reports active.
    """
    if os.name != "nt":
        return False
    if os.environ.get("SFFS_OS_ISOLATION") == "windows_job" and os.environ.get("SFFS_JOB_OBJECT_ACTIVE") == "1":
        return True

    global _SFFS_JOB_HANDLE
    if _SFFS_JOB_HANDLE:
        os.environ["SFFS_OS_ISOLATION"] = "windows_job"
        os.environ["SFFS_JOB_OBJECT_ACTIVE"] = "1"
        return True

    try:
        hjob = _create_job_object()
        _check_bool(
            kernel32.AssignProcessToJobObject(ctypes.c_void_p(hjob), _CURRENT_PROCESS_PSEUDO),
            "AssignProcessToJobObject failed",
        )
    except OSError:
        return False

    _SFFS_JOB_HANDLE = hjob
    os.environ["SFFS_OS_ISOLATION"] = "windows_job"
    os.environ["SFFS_JOB_OBJECT_ACTIVE"] = "1"
    return True


def main() -> int:
    if os.name != "nt":
        print("windows_job_wrapper.py is only supported on Windows.", file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parent.parent
    main_py = repo_root / "main-code" / "main.py"
    args = [sys.executable, str(main_py), "--secure-required", *sys.argv[1:]]

    env = dict(os.environ)
    env["SFFS_OS_ISOLATION"] = "windows_job"
    env["SFFS_JOB_OBJECT_ACTIVE"] = "1"

    hjob = _create_job_object()
    try:
        child = subprocess.Popen(args, env=env, cwd=str(repo_root),
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        _assign_process_to_job(hjob, child.pid)
        return child.wait()
    finally:
        kernel32.CloseHandle(hjob)


if __name__ == "__main__":
    raise SystemExit(main())
