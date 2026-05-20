"""
hidden_volume.py — Windows API for hidden partition discovery and mount.

Enumerates all volumes, finds the one with .sffs_marker (no drive letter),
and mounts it temporarily to a drive letter using DefineDosDeviceW.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from pathlib import Path

kernel32 = ctypes.windll.kernel32

# Set correct return/arg types to prevent 64-bit handle truncation
kernel32.FindFirstVolumeW.restype = ctypes.c_void_p
kernel32.FindFirstVolumeW.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong]
kernel32.FindNextVolumeW.restype = ctypes.wintypes.BOOL
kernel32.FindNextVolumeW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong]
kernel32.FindVolumeClose.restype = ctypes.wintypes.BOOL
kernel32.FindVolumeClose.argtypes = [ctypes.c_void_p]
kernel32.GetVolumePathNamesForVolumeNameW.restype = ctypes.wintypes.BOOL
kernel32.GetVolumePathNamesForVolumeNameW.argtypes = [
    ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)
]
kernel32.DefineDosDeviceW.restype = ctypes.wintypes.BOOL
kernel32.DefineDosDeviceW.argtypes = [ctypes.wintypes.DWORD, ctypes.c_wchar_p, ctypes.c_wchar_p]
kernel32.SetVolumeMountPointW.restype = ctypes.wintypes.BOOL
kernel32.SetVolumeMountPointW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
kernel32.DeleteVolumeMountPointW.restype = ctypes.wintypes.BOOL
kernel32.DeleteVolumeMountPointW.argtypes = [ctypes.c_wchar_p]
kernel32.GetDriveTypeW.restype = ctypes.c_uint
kernel32.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
kernel32.GetVolumeInformationW.restype = ctypes.wintypes.BOOL
kernel32.GetVolumeInformationW.argtypes = [
    ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_ulong,
    ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
    ctypes.POINTER(ctypes.c_ulong), ctypes.c_wchar_p, ctypes.c_ulong,
]

MAX_PATH = 260
VOLUME_NAME_BUFFER = 512

# DefineDosDeviceW flags
DDD_RAW_TARGET_PATH = 0x00000001
DDD_REMOVE_DEFINITION = 0x00000002
DDD_EXACT_MATCH_ON_REMOVE = 0x00000004

# GetDriveType return values
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3
DRIVE_REMOTE = 4
DRIVE_CDROM = 5
DRIVE_RAMDISK = 6


def _get_drive_type(path: str) -> int:
    return kernel32.GetDriveTypeW(path)


def _is_removable(volume_guid: str) -> bool:
    """Check if a volume is on a removable drive."""
    # Try to get a mount point for this volume
    buf = ctypes.create_unicode_buffer(VOLUME_NAME_BUFFER)
    result = kernel32.GetVolumePathNamesForVolumeNameW(
        volume_guid, buf, VOLUME_NAME_BUFFER, ctypes.byref(ctypes.c_ulong())
    )
    if result:
        path = buf.value
        if path:
            drive_type = _get_drive_type(path)
            return drive_type == DRIVE_REMOVABLE
    # If we can't get a mount point, check all removable drives
    return False


def enumerate_volumes() -> list[str]:
    """Enumerate all volume GUID paths on the system."""
    _INVALID = ctypes.c_void_p(-1).value  # 0xFFFF... or -1 depending on Python build
    volumes = []
    buf = ctypes.create_unicode_buffer(VOLUME_NAME_BUFFER)
    handle = kernel32.FindFirstVolumeW(buf, VOLUME_NAME_BUFFER)
    if handle is None or handle == _INVALID or handle == 0:
        return volumes
    try:
        volumes.append(buf.value)
        while True:
            result = kernel32.FindNextVolumeW(handle, buf, VOLUME_NAME_BUFFER)
            if not result:
                break
            volumes.append(buf.value)
    finally:
        kernel32.FindVolumeClose(handle)
    return volumes


def volume_has_marker(volume_guid: str, marker: str = ".sffs_marker") -> bool:
    """Check if a volume contains the marker file at its root."""
    # Try to find a mount point for this volume
    buf = ctypes.create_unicode_buffer(VOLUME_NAME_BUFFER * 4)
    needed = ctypes.c_ulong()
    result = kernel32.GetVolumePathNamesForVolumeNameW(
        volume_guid, buf, VOLUME_NAME_BUFFER * 4, ctypes.byref(needed)
    )
    if result:
        # Volume already has a mount point — check if marker exists
        mount = buf.value
        if mount:
            marker_path = Path(mount) / marker
            return marker_path.exists()
    return False


def volume_has_no_drive_letter(volume_guid: str) -> bool:
    """Check if a volume has no drive letter assigned (is 'hidden')."""
    buf = ctypes.create_unicode_buffer(VOLUME_NAME_BUFFER * 4)
    needed = ctypes.c_ulong()
    result = kernel32.GetVolumePathNamesForVolumeNameW(
        volume_guid, buf, VOLUME_NAME_BUFFER * 4, ctypes.byref(needed)
    )
    if not result:
        return True  # No mount points at all
    mount = buf.value
    if not mount:
        return True  # Empty mount list
    # Check if mount is a drive letter (e.g., "C:\")
    return len(mount.strip()) > 3 or not mount[1] == ':'


def find_hidden_partition(marker: str = ".sffs_marker") -> str | None:
    """
    Enumerate volumes and find the one with the marker file and no drive letter.

    Returns volume GUID path like \\\\?\\Volume{xxx}\\, or None.
    """
    for vol in enumerate_volumes():
        if not vol.endswith("\\"):
            vol += "\\"
        if volume_has_marker(vol, marker):
            return vol
    return None


def _volume_label(volume_guid: str) -> str:
    """Return volume label using GUID path (works without a drive letter assigned)."""
    buf = ctypes.create_unicode_buffer(256)
    r = kernel32.GetVolumeInformationW(volume_guid, buf, 256, None, None, None, None, 0)
    return buf.value if r else ""


def find_sffs_partition(marker: str = ".sffs_marker") -> str | None:
    """
    Find the SFFS partition.
    Identifies by volume label "SFFS_DATA" (works without mounting).
    Falls back to marker-file check for already-mounted volumes.

    Returns volume GUID path like \\\\?\\Volume{xxx}\\, or None.
    """
    # Primary: hidden partition identified by label (no mount needed)
    for vol in enumerate_volumes():
        guid = vol if vol.endswith("\\") else vol + "\\"
        if volume_has_no_drive_letter(guid) and _volume_label(guid) == "SFFS_DATA":
            return guid

    # Fallback: any partition with SFFS_DATA label (already mounted)
    for vol in enumerate_volumes():
        guid = vol if vol.endswith("\\") else vol + "\\"
        if _volume_label(guid) == "SFFS_DATA":
            return guid

    # Last resort: marker file check (volume must already have a mount point)
    for vol in enumerate_volumes():
        guid = vol if vol.endswith("\\") else vol + "\\"
        if volume_has_marker(guid, marker):
            return guid

    return None


def mount_hidden_volume(
    volume_guid: str,
    drive_letter: str = "S",
) -> bool:
    """
    Mount a hidden volume to a drive letter using SetVolumeMountPointW.

    Uses the same API as `mountvol` — assigns a real Windows volume mount,
    not a raw DOS device alias (which DefineDosDeviceW would create).

    Args:
        volume_guid: Volume GUID path like \\\\?\\Volume{xxx}\\
        drive_letter: Single letter (e.g., "S") — will become S:

    Returns:
        True if mount succeeded.
    """
    mount_point = f"{drive_letter}:\\"
    guid = volume_guid if volume_guid.endswith("\\") else volume_guid + "\\"
    # Remove any existing mapping first (ignore errors — may not exist)
    kernel32.DeleteVolumeMountPointW(mount_point)
    result = kernel32.SetVolumeMountPointW(mount_point, guid)
    return bool(result)


def unmount_hidden_volume(drive_letter: str = "S") -> bool:
    """
    Remove a drive letter mount using DeleteVolumeMountPointW.

    Args:
        drive_letter: Single letter (e.g., "S")

    Returns:
        True if unmount succeeded.
    """
    mount_point = f"{drive_letter}:\\"
    result = kernel32.DeleteVolumeMountPointW(mount_point)
    return bool(result)


def get_mounted_path(drive_letter: str = "S") -> Path:
    """Return Path for the mounted drive letter."""
    return Path(f"{drive_letter}:\\")


if __name__ == "__main__":
    print("=== SFFS Hidden Volume Discovery ===\n")

    print("All volumes:")
    for vol in enumerate_volumes():
        has_marker = volume_has_marker(vol)
        has_letter = not volume_has_no_drive_letter(vol)
        letter = "HIDDEN" if not has_letter else "MOUNTED"
        marker = " [SFFS]" if has_marker else ""
        print(f"  {vol}  ({letter}{marker})")

    print()
    hidden = find_hidden_partition()
    if hidden:
        print(f"Found hidden SFFS partition: {hidden}")
        if mount_hidden_volume(hidden):
            print("Mounted to S:\\")
            print(f"Contents: {list(Path('S:\\').iterdir())}")
            input("Press Enter to unmount...")
            unmount_hidden_volume()
            print("Unmounted.")
    else:
        print("No hidden SFFS partition found.")
        sffs = find_sffs_partition()
        if sffs:
            print(f"Found SFFS partition (mounted): {sffs}")
        else:
            print("No SFFS partition found at all.")
