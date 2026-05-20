"""
f13_init_drive_detection.py — SFFS Student 3: USB / portable path layout

Portable deployments cannot hardcode drive letters (Windows) or fixed mount paths
(Linux): the OS assigns different roots when the USB is reinserted. This module
resolves the application directory from ``sys.argv[0]``, finds the volume root,
and returns a single path map used by every other module.

WHY ``sys.argv[0]`` for app_dir:
- Reflects the entry script (e.g. main-code/main.py), not necessarily this file.

WHY other modules must not invent their own roots:
- One source of truth avoids split-brain paths (keys on one drive, logs on another).

Dependencies: ``psutil`` for partition/removable detection (especially Linux).
"""

from __future__ import annotations

import os
import platform
import sys
import threading
import time
import warnings
from pathlib import Path

# Why: cross-platform disk/partition enumeration; raw os.listdir("/") is not portable
import psutil


def _resolved_script_parent() -> Path:
    return Path(sys.argv[0]).resolve().parent


def _windows_volume_root(path: Path) -> Path:
    p = path.resolve()
    anchor = p.anchor  # e.g. "D:\\"
    return Path(anchor)


def _linux_mount_root(path: Path) -> Path:
    p = str(path.resolve())
    best = "/"
    best_len = 0
    for part in psutil.disk_partitions(all=False):
        m = part.mountpoint
        if p == m or p.startswith(m.rstrip("/") + os.sep):
            if len(m) > best_len:
                best = m
                best_len = len(m)
    return Path(best)


def _partition_for_path(path: Path) -> tuple[str | None, bool, str]:
    """Return (device, is_removable_guess, opts) for path's volume."""
    sysname = platform.system()
    p = path.resolve()
    if sysname == "Windows":
        for part in psutil.disk_partitions(all=False):
            try:
                if str(p).upper().startswith(part.mountpoint.upper()):
                    opts = part.opts or ""
                    removable = "removable" in opts.lower()
                    return part.device, removable, opts
            except (OSError, ValueError):
                continue
        drive = p.drive + "\\"
        return drive, False, ""
    for part in psutil.disk_partitions(all=False):
        m = part.mountpoint
        if str(p).startswith(m.rstrip("/") + os.sep) or str(p) == m.rstrip("/"):
            opts = part.opts or ""
            removable = "removable" in opts.lower()
            return part.device, removable, opts
    return None, False, ""


def getAvailableSpace(path: Path) -> dict:
    """
    Return disk usage for the filesystem containing ``path``.

    Args:
        path: Any path on the target filesystem.

    Returns:
        dict with total_gb, used_gb, free_gb.
    """
    usage = psutil.disk_usage(str(path))
    gb = 1024 ** 3
    return {
        "total_gb": round(usage.total / gb, 3),
        "used_gb": round((usage.total - usage.free) / gb, 3),
        "free_gb": round(usage.free / gb, 3),
    }


def initDriveDetection() -> dict:
    """
    Detect USB (or development) root and create standard SFFS directories.

    Returns:
        dict with usb_root, app_dir, data_dir, keys_dir, sandbox_dir, logs_dir,
        config_dir, backups_dir, platform, is_removable, drive_label, free_space_gb.
    """
    app_dir = _resolved_script_parent()
    sysname = platform.system()
    if sysname == "Windows":
        volume_root = _windows_volume_root(app_dir)
    else:
        volume_root = _linux_mount_root(app_dir)

    _, is_removable, opts = _partition_for_path(app_dir)
    if not is_removable:
        warnings.warn(
            "SFFS is not running from a removable volume (development mode). "
            f"Partition opts: {opts!r}. Using repository root for sffs_data.",
            UserWarning,
            stacklevel=2,
        )
        # Avoid littering the OS volume root (e.g. C:\\sffs_data) during local dev
        usb_root = app_dir.resolve().parent
    else:
        usb_root = volume_root

    try:
        label = usb_root.name or str(usb_root)
    except Exception:
        label = str(usb_root)

    data_dir = usb_root / "sffs_data"
    paths_map = {
        "usb_root": usb_root,
        "app_dir": app_dir,
        "data_dir": data_dir,
        "keys_dir": data_dir / "keys",
        "sandbox_dir": data_dir / "sandbox",
        "logs_dir": data_dir / "logs",
        "config_dir": data_dir / "config",
        "backups_dir": data_dir / "backups",
        "platform": sysname,
        "is_removable": is_removable,
        "drive_label": label,
        "free_space_gb": getAvailableSpace(usb_root)["free_gb"],
    }
    for key in (
        "data_dir",
        "keys_dir",
        "sandbox_dir",
        "logs_dir",
        "config_dir",
        "backups_dir",
    ):
        paths_map[key].mkdir(parents=True, exist_ok=True)
    return paths_map


def monitorUSBPresence(usb_root: Path, callback, interval_seconds: float = 0.5) -> threading.Thread:
    """
    Background thread: invoke ``callback`` when ``usb_root`` stops existing.

    Args:
        usb_root: Root path to watch.
        callback: Callable with no arguments.
        interval_seconds: Poll interval.

    Returns:
        Started daemon thread.
    """

    def _run() -> None:
        while True:
            time.sleep(interval_seconds)
            if not usb_root.exists():
                try:
                    callback()
                except Exception:
                    pass
                break

    t = threading.Thread(target=_run, daemon=True, name="SFFS-USBWatch")
    t.start()
    return t


if __name__ == "__main__":
    m = initDriveDetection()
    print("Path map:")
    for k, v in m.items():
        print(f"  {k}: {v}")
    print("Space:", getAvailableSpace(m["usb_root"]))
