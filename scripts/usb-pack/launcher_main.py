"""
launcher_main.py — SFFS Launcher Entry Point

Finds the hidden partition with .sffs_marker, mounts it to S:\,
then spawns the SFFS application from the hidden partition.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from pathlib import Path

# Add sibling directory to path for hidden_volume import
_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from hidden_volume import (
    mount_hidden_volume,
    unmount_hidden_volume,
)

DRIVE_LETTER = "S"
CREATE_NO_WINDOW = 0x08000000


def _find_sffs_volume_guid() -> "str | None":
    """Find SFFS hidden partition GUID. Tries four strategies in order."""
    exe_path = Path(sys.executable if getattr(sys, "frozen", False) else sys.argv[0])

    # Strategy 0: GUID file next to the exe — fastest, set by rebuild bat
    try:
        guid_file = exe_path.parent / "sffs_volume.guid"
        if guid_file.exists():
            saved = guid_file.read_text(encoding="utf-8").strip()
            if saved and "Volume{" in saved:
                return saved if saved.endswith("\\") else saved + "\\"
    except Exception:
        pass

    # Strategy 1: PowerShell — same-disk sibling partition (no drive letter, NTFS)
    try:
        drive = exe_path.drive[0] if exe_path.drive else None
        if drive:
            cmd = (
                "$d=(Get-Partition -DriveLetter '" + drive + "').DiskNumber; "
                "Get-Partition -DiskNumber $d "
                "| Where-Object {$_.DriveLetter -eq $null} "
                "| Get-Volume "
                "| Where-Object {$_.FileSystem -eq 'NTFS'} "
                "| Select-Object -ExpandProperty UniqueId"
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
                capture_output=True, text=True, timeout=15,
                creationflags=CREATE_NO_WINDOW,
            )
            uid = r.stdout.strip()
            if uid and "Volume{" in uid:
                return uid if uid.endswith("\\") else uid + "\\"
    except Exception:
        pass

    # Strategy 2: PowerShell — label scan for SFFS_DATA across all volumes
    try:
        cmd = (
            "(Get-Volume "
            "| Where-Object {$_.FileSystemLabel -eq 'SFFS_DATA'} "
            "| Select-Object -First 1 -ExpandProperty UniqueId)"
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
            capture_output=True, text=True, timeout=15,
            creationflags=CREATE_NO_WINDOW,
        )
        uid = r.stdout.strip()
        if uid and "Volume{" in uid:
            return uid if uid.endswith("\\") else uid + "\\"
    except Exception:
        pass

    # Strategy 3: ctypes fallback via hidden_volume
    try:
        from hidden_volume import find_sffs_partition
        return find_sffs_partition()
    except Exception:
        pass

    return None


def _is_admin() -> bool:
    """Check if running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _run_as_admin() -> None:
    """Relaunch this script with admin privileges."""
    exe = sys.executable
    script = sys.argv[0]
    args = sys.argv[1:]
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", exe, f'"{script}" {" ".join(args)}', None, 1
    )
    sys.exit(0)


def _show_error(title: str, message: str) -> None:
    """Show a Windows message box."""
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
    except Exception:
        print(f"[{title}] {message}", file=sys.stderr)


def main() -> int:
    # Step 1: Find the hidden SFFS partition
    volume_guid = _find_sffs_volume_guid()
    if not volume_guid:
        _show_error(
            "SFFS Launcher",
            "No SFFS partition found.\n\n"
            "Make sure the USB is plugged in and has been set up with "
            "sffs_usb_pack.py.",
        )
        return 1

    # Step 2: Try to mount the hidden volume
    if not mount_hidden_volume(volume_guid, DRIVE_LETTER):
        # Mount failed — likely needs admin
        if not _is_admin():
            _run_as_admin()
            return 0  # Admin process replaces us
        else:
            _show_error(
                "SFFS Launcher",
                f"Failed to mount hidden partition to {DRIVE_LETTER}:\\.\n\n"
                "Please run as Administrator and try again.",
            )
            return 1

    try:
        # Step 3: Verify the mount — check main-code dir exists on hidden partition
        root = Path(f"{DRIVE_LETTER}:\\")
        if not root.exists() or not (root / "main-code").exists():
            _show_error("SFFS Launcher", f"Mount verification failed: {root}")
            return 1

        # Step 4: Find Python and main entry point on hidden partition
        python_exe = root / "python" / "python.exe"
        main_py = root / "main-code" / "main.py"

        if not python_exe.exists():
            _show_error(
                "SFFS Launcher",
                f"Python not found on hidden partition:\n{python_exe}",
            )
            return 1

        if not main_py.exists():
            _show_error(
                "SFFS Launcher",
                f"Main entry point not found on hidden partition:\n{main_py}",
            )
            return 1

        # Step 5: Spawn the SFFS application
        env = os.environ.copy()
        env["SFFS_ROOT"] = str(root)
        env["PYTHONPATH"] = (
            str(root / "code1") + os.pathsep
            + str(root / "code2") + os.pathsep
            + str(root / "code3") + os.pathsep
            + str(root / "main-code") + os.pathsep
            + env.get("PYTHONPATH", "")
        )

        cmd = [str(python_exe), str(main_py)] + sys.argv[1:]
        proc = subprocess.run(cmd, env=env)
        return proc.returncode

    finally:
        # Step 6: Unmount the hidden partition
        unmount_hidden_volume(DRIVE_LETTER)


if __name__ == "__main__":
    raise SystemExit(main())
