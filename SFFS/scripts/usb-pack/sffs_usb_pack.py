"""
sffs_usb_pack.py — Full USB automation for SFFS portable deployment.

Partitions a USB drive into visible (NTFS) + hidden (NTFS) partitions,
installs Python embeddable on the hidden partition, builds PyInstaller
executables, and copies everything into place.

Usage:
    python sffs_usb_pack.py          # Interactive: select drive, partition, build
    python sffs_usb_pack.py --drive E  # Non-interactive: use drive E:
    python sffs_usb_pack.py --list    # List available removable drives
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

# Add sibling directory to path
_script_dir = Path(__file__).resolve().parent
_sffs_root = _script_dir.parent.parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from hidden_volume import (
    enumerate_volumes,
    find_sffs_partition,
    mount_hidden_volume,
    unmount_hidden_volume,
)

# ─── Configuration ───────────────────────────────────────────────────────────

PYTHON_VERSION = "3.14.3"
PYTHON_EMBED_URL = (
    f"https://www.python.org/ftp/python/{PYTHON_VERSION}/"
    f"python-{PYTHON_VERSION}-embed-amd64.zip"
)
PYTHON_EMBED_FALLBACK_URL = (
    "https://www.python.org/ftp/python/3.13.5/python-3.13.5-embed-amd64.zip"
)
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

HIDDEN_SIZE_MB = 2048  # 2 GB hidden partition (fixed)
# Visible partition takes all remaining space on the drive

DRIVE_LETTER_MOUNT = "S"  # Temporary mount letter for hidden partition

# ─── Helpers ─────────────────────────────────────────────────────────────────


def log(msg: str, level: str = "INFO") -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def run_cmd(cmd: list[str], check: bool = True, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    log(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.stdout.strip():
        for line in result.stdout.strip().split("\n"):
            log(f"  stdout: {line}")
    if result.stderr.strip():
        for line in result.stderr.strip().split("\n"):
            log(f"  stderr: {line}", level="WARN")
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed (rc={result.returncode}): {' '.join(cmd)}"
        )
    return result


def run_diskpart(script: str) -> None:
    """Run a diskpart script."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(script)
        f.flush()
        temp_path = f.name

    try:
        run_cmd(["diskpart", "/s", temp_path], timeout=120)
    finally:
        os.unlink(temp_path)


# ─── Step 1: Detect USB drives ───────────────────────────────────────────────


def list_removable_drives() -> list[dict]:
    """List all removable drives with their details."""
    drives = []
    import shutil
    import string

    for letter in string.ascii_uppercase:
        path = f"{letter}:\\"
        try:
            usage = shutil.disk_usage(path)
            total_gb = usage.total / (1024**3)
            free_gb = usage.free / (1024**3)
            drives.append(
                {
                    "letter": letter,
                    "path": path,
                    "total_gb": round(total_gb, 1),
                    "free_gb": round(free_gb, 1),
                }
            )
        except OSError:
            continue
    return drives


def select_drive(interactive: bool = True, target: str | None = None) -> str:
    """Let user select a USB drive."""
    drives = list_removable_drives()
    if not drives:
        raise RuntimeError("No removable drives found.")

    if target:
        target = target.upper().rstrip(":")
        for d in drives:
            if d["letter"] == target:
                log(f"Selected drive {target}: ({d['total_gb']} GB total)")
                return target
        raise RuntimeError(f"Drive {target}: not found or not accessible.")

    if interactive:
        print("\nAvailable removable drives:")
        print("-" * 40)
        for i, d in enumerate(drives, 1):
            print(f"  {i}. {d['letter']}:  ({d['total_gb']} GB total, {d['free_gb']} GB free)")
        print()
        while True:
            choice = input("Select drive number (or letter): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(drives):
                    return drives[idx]["letter"]
            elif len(choice) == 1 and choice.isalpha():
                letter = choice.upper()
                if any(d["letter"] == letter for d in drives):
                    return letter
            print("Invalid selection. Try again.")
    else:
        # Auto-select the first removable drive
        return drives[0]["letter"]


# ─── Step 2: Partition the USB ──────────────────────────────────────────────


def partition_usb(drive_letter: str) -> tuple[str, str]:
    """
    Wipe and repartition the USB drive.

    Returns (visible_letter, hidden_volume_guid).
    """
    log(f"Partitioning drive {drive_letter}: ...")

    # First, get the disk number for this drive
    disk_num = _get_disk_number(drive_letter)
    log(f"Drive {drive_letter}: is on disk {disk_num}")

    # Create diskpart script
    diskpart_script = f"""
select disk {disk_num}
clean
create partition primary size={HIDDEN_SIZE_MB}
format quick fs=ntfs label="SFFS_DATA"
create partition primary
format quick fs=ntfs label="SFFS"
assign letter={drive_letter}
exit
"""

    run_diskpart(diskpart_script)
    log(f"Partitioned: {HIDDEN_SIZE_MB}MB hidden + remaining space visible")

    # Find the hidden partition's volume GUID
    hidden_guid = _find_hidden_volume_guid(disk_num)
    if not hidden_guid:
        raise RuntimeError("Could not find hidden partition volume GUID.")

    log(f"Hidden partition GUID: {hidden_guid}")
    return drive_letter, hidden_guid


def _get_disk_number(drive_letter: str) -> int:
    """Get the disk number for a given drive letter."""
    result = run_cmd(
        ["powershell", "-Command",
         f"(Get-Partition -DriveLetter '{drive_letter}').DiskNumber"],
    )
    return int(result.stdout.strip())


def _find_hidden_volume_guid(disk_num: int) -> str | None:
    """Find the volume GUID for the hidden partition on the given disk."""
    result = run_cmd(
        ["powershell", "-Command",
         f"Get-Partition -DiskNumber {disk_num} | Where-Object {{ $_.DriveLetter -eq $null }} | Get-Volume | Where-Object {{ $_.FileSystem -eq 'NTFS' }} | Select-Object -ExpandProperty ObjectId"],
    )
    # ObjectId looks like: \\?\Volume{GUID}\
    output = result.stdout.strip()
    if output and "Volume{" in output:
        # Extract the GUID path
        start = output.index("\\\\?\\")
        end = output.index("\\", start + 4) + 1
        return output[start:end]
    return None


# ─── Step 3: Mount hidden partition temporarily ──────────────────────────────


def mount_for_setup(hidden_guid: str, temp_letter: str = "X") -> str:
    """Mount the hidden partition for setup."""
    log(f"Mounting hidden partition to {temp_letter}: ...")
    if mount_hidden_volume(hidden_guid, temp_letter):
        log(f"Mounted to {temp_letter}:")
        return temp_letter

    # Fallback: use mountvol
    try:
        run_cmd(["mountvol", f"{temp_letter}:", hidden_guid])
        log(f"Mounted via mountvol to {temp_letter}:")
        return temp_letter
    except Exception:
        raise RuntimeError(f"Failed to mount hidden partition to {temp_letter}:")


def unmount_for_setup(temp_letter: str = "X") -> None:
    """Unmount the temporary mount."""
    log(f"Unmounting {temp_letter}: ...")
    try:
        unmount_hidden_volume(temp_letter)
    except Exception:
        try:
            run_cmd(["mountvol", f"{temp_letter}:", "/d"])
        except Exception:
            pass
    log(f"Unmounted {temp_letter}:")


# ─── Step 4: Download and install Python embeddable ──────────────────────────


def download_python_embeddable(target_dir: Path) -> Path:
    """Download and extract Python embeddable distribution."""
    log(f"Downloading Python {PYTHON_VERSION} embeddable...")
    zip_path = target_dir / "python_embed.zip"

    try:
        urllib.request.urlretrieve(PYTHON_EMBED_URL, zip_path)
    except Exception:
        log(f"Primary download failed, trying fallback...", "WARN")
        urllib.request.urlretrieve(PYTHON_EMBED_FALLBACK_URL, zip_path)

    log(f"Extracting Python embeddable...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target_dir)

    zip_path.unlink()

    # Find the extracted python.exe
    python_exe = target_dir / "python.exe"
    if not python_exe.exists():
        # Sometimes it extracts into a subdirectory
        for p in target_dir.rglob("python.exe"):
            python_exe = p
            break

    if not python_exe.exists():
        raise RuntimeError("python.exe not found after extraction.")

    log(f"Python embeddable installed at: {python_exe}")
    return python_exe


def install_pip(python_exe: Path) -> None:
    """Install pip into the embeddable Python."""
    log("Installing pip...")
    get_pip_path = python_exe.parent / "get-pip.py"
    urllib.request.urlretrieve(GET_PIP_URL, get_pip_path)

    # Enable site-packages in embeddable Python
    pth_file = python_exe.parent / f"python{sys.version_info.major}{sys.version_info.minor}._pth"
    if not pth_file.exists():
        # Try to find the .pth file
        for p in python_exe.parent.glob("python*._pth"):
            pth_file = p
            break

    if pth_file.exists():
        content = pth_file.read_text(encoding="utf-8")
        if "import site" not in content:
            content += "\nimport site\n"
            pth_file.write_text(content, encoding="utf-8")
            log("Enabled site-packages in embeddable Python.")

    run_cmd([str(python_exe), str(get_pip_path)])
    get_pip_path.unlink()
    log("pip installed.")


def install_dependencies(python_exe: Path) -> None:
    """Install SFFS dependencies."""
    log("Installing SFFS dependencies...")
    requirements = _sffs_root / "main-code" / "requirements.txt"
    if not requirements.exists():
        raise FileNotFoundError(f"requirements.txt not found: {requirements}")

    run_cmd([str(python_exe), "-m", "pip", "install", "-r", str(requirements)])
    log("Dependencies installed.")


# ─── Step 5: Copy SFFS source code ──────────────────────────────────────────


def copy_source_code(hidden_root: Path) -> None:
    """Copy SFFS source code to the hidden partition."""
    log("Copying SFFS source code to hidden partition...")

    dirs_to_copy = ["code1", "code2", "code3", "main-code"]
    for dirname in dirs_to_copy:
        src = _sffs_root / dirname
        dst = hidden_root / dirname
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            # Remove __pycache__ and test_output
            for p in dst.rglob("__pycache__"):
                if p.is_dir():
                    shutil.rmtree(p)
            for p in dst.rglob("test_output"):
                if p.is_dir():
                    shutil.rmtree(p)
            log(f"  Copied {dirname}/")

    # Also copy the hidden_volume.py to main-code for the worker
    hv_src = _script_dir / "hidden_volume.py"
    hv_dst = hidden_root / "main-code" / "hidden_volume.py"
    shutil.copy2(hv_src, hv_dst)
    log("  Copied hidden_volume.py")

    # Create sffs_data directory structure
    sffs_data = hidden_root / "sffs_data"
    for subdir in ["keys", "logs", "config", "sandbox", "backups"]:
        (sffs_data / subdir).mkdir(parents=True, exist_ok=True)
    log("  Created sffs_data/ structure")


# ─── Step 6: Generate icon ──────────────────────────────────────────────────


def generate_icon() -> Path:
    """Generate the SFFS icon."""
    log("Generating SFFS icon...")
    icon_path = _script_dir / "sffs.ico"

    try:
        from generate_icon import generate_ico
        generate_ico(icon_path)
    except ImportError:
        log("Pillow not available, using placeholder icon.", "WARN")
        # Create a minimal placeholder .ico
        _create_placeholder_icon(icon_path)

    return icon_path


def _create_placeholder_icon(path: Path) -> None:
    """Create a minimal placeholder .ico file."""
    # Create a 32x32 blue square as a placeholder
    import struct

    def create_ico(size: int) -> bytes:
        # ICO header: 0, 1 (icon), 1 image
        header = struct.pack("<HHH", 0, 1, 1)
        # ICO directory entry
        entry = struct.pack(
            "<BBBBHHII",
            size, size, 0, 0, 1, 32,
            40 + size * size * 4,  # data offset
            40 + size * size * 4,  # data size
        )
        # BMP header (BITMAPINFOHEADER)
        bmp_header = struct.pack(
            "<IiiHHIIiiII",
            40, size, size * 2, 1, 32, 0, 0, 0, 0, 0, 0,
        )
        # Pixel data (blue square, bottom-up)
        pixels = b""
        for y in range(size * 2):
            for x in range(size):
                if y < size:
                    pixels += b"\x00\x00\xff\xff"  # Blue
                else:
                    pixels += b"\x00\x00\x00\x00"  # Transparent
        return header + entry + bmp_header + pixels

    path.write_bytes(create_ico(32))
    log(f"Placeholder icon created: {path}")


# ─── Step 7: Build PyInstaller executables ───────────────────────────────────


def build_executables(icon_path: Path) -> tuple[Path, Path]:
    """Build SFFS_launcher.exe and SFFS_worker.exe."""
    log("Building executables with PyInstaller...")

    # Check PyInstaller is installed
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        log("Installing PyInstaller...", "WARN")
        run_cmd([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Build launcher
    log("Building SFFS_launcher.exe...")
    run_cmd([
        sys.executable, "-m", "PyInstaller",
        str(_script_dir / "sffs_bootstrap.spec"),
        "--distpath", str(_script_dir / "dist"),
        "--workpath", str(_script_dir / "build"),
        "--noconfirm",
    ], timeout=600)

    launcher_exe = _script_dir / "dist" / "SFFS_launcher.exe"
    if not launcher_exe.exists():
        raise RuntimeError(f"Launcher build failed: {launcher_exe} not found.")
    log(f"Launcher built: {launcher_exe} ({launcher_exe.stat().st_size / 1024 / 1024:.1f} MB)")

    # Build worker
    log("Building SFFS_worker.exe...")
    run_cmd([
        sys.executable, "-m", "PyInstaller",
        str(_script_dir / "sffs_worker.spec"),
        "--distpath", str(_script_dir / "dist"),
        "--workpath", str(_script_dir / "build"),
        "--noconfirm",
    ], timeout=600)

    worker_exe = _script_dir / "dist" / "SFFS_worker.exe"
    if not worker_exe.exists():
        raise RuntimeError(f"Worker build failed: {worker_exe} not found.")
    log(f"Worker built: {worker_exe} ({worker_exe.stat().st_size / 1024 / 1024:.1f} MB)")

    return launcher_exe, worker_exe


# ─── Step 8: Copy to visible partition ───────────────────────────────────────


def copy_to_visible_partition(
    visible_drive: str,
    launcher_exe: Path,
    worker_exe: Path,
) -> None:
    """Copy executables, autorun.inf, README, and source to visible partition."""
    log(f"Copying to visible partition {visible_drive}: ...")
    visible_root = Path(f"{visible_drive}:\\")

    # Copy executables
    shutil.copy2(launcher_exe, visible_root / "SFFS_launcher.exe")
    shutil.copy2(worker_exe, visible_root / "SFFS_worker.exe")
    log("  Copied executables")

    # Copy source code for Linux fallback
    dirs_to_copy = ["code1", "code2", "code3", "main-code"]
    for dirname in dirs_to_copy:
        src = _sffs_root / dirname
        dst = visible_root / dirname
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            # Remove __pycache__ and test_output
            for p in dst.rglob("__pycache__"):
                if p.is_dir():
                    shutil.rmtree(p)
            for p in dst.rglob("test_output"):
                if p.is_dir():
                    shutil.rmtree(p)
            log(f"  Copied {dirname}/")

    # Create autorun.inf
    autorun = visible_root / "autorun.inf"
    autorun.write_text(
        "[AutoRun]\n"
        "open=SFFS_launcher.exe\n"
        "action=Run SFFS\n"
        "icon=SFFS_launcher.exe,0\n"
        "label=SFFS - Smart File Fortify System\n",
        encoding="utf-8",
    )
    log("  Created autorun.inf")

    # Create README.txt
    readme = visible_root / "README.txt"
    readme.write_text(
        "SFFS - Smart File Fortify System\n"
        "=" * 40 + "\n\n"
        "Windows: Double-click SFFS_launcher.exe to run.\n\n"
        "Linux: Copy the source code directories (code1/, code2/, code3/, main-code/)\n"
        "to a local directory, install dependencies (pip install -r main-code/requirements.txt),\n"
        "and run: python main-code/main.py\n\n"
        "For more information, see docs/ in the source code.\n",
        encoding="utf-8",
    )
    log("  Created README.txt")


# ─── Step 9: Create marker file ─────────────────────────────────────────────


def create_marker(hidden_root: Path) -> None:
    """Create the .sffs_marker file on the hidden partition."""
    marker = hidden_root / ".sffs_marker"
    marker.write_text(
        "SFFS Hidden Partition\n"
        "Do not delete this file.\n"
        f"Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        encoding="utf-8",
    )
    log(f"Created marker file: {marker}")


# ─── Step 10: Verify ────────────────────────────────────────────────────────


def verify_setup(visible_drive: str, hidden_guid: str) -> bool:
    """Verify the USB setup is complete and correct."""
    log("Verifying USB setup...")
    errors = []

    # Check visible partition
    visible_root = Path(f"{visible_drive}:\\")
    checks = [
        (visible_root / "SFFS_launcher.exe", "Launcher executable"),
        (visible_root / "SFFS_worker.exe", "Worker executable"),
        (visible_root / "autorun.inf", "Autorun file"),
        (visible_root / "README.txt", "README file"),
        (visible_root / "code1", "Code1 directory"),
        (visible_root / "code2", "Code2 directory"),
        (visible_root / "code3", "Code3 directory"),
        (visible_root / "main-code", "Main-code directory"),
    ]

    for path, desc in checks:
        if path.exists():
            log(f"  [OK] {desc}")
        else:
            log(f"  [FAIL] {desc}: {path}", "ERROR")
            errors.append(desc)

    # Check hidden partition
    temp_letter = "V"
    try:
        if not mount_hidden_volume(hidden_guid, temp_letter):
            errors.append("Cannot mount hidden partition for verification")
            return False

        hidden_root = Path(f"{temp_letter}:\\")
        hidden_checks = [
            (hidden_root / ".sffs_marker", "Marker file"),
            (hidden_root / "python" / "python.exe", "Python executable"),
            (hidden_root / "code1", "Code1 directory"),
            (hidden_root / "code2", "Code2 directory"),
            (hidden_root / "code3", "Code3 directory"),
            (hidden_root / "main-code", "Main-code directory"),
            (hidden_root / "sffs_data", "sffs_data directory"),
        ]

        for path, desc in hidden_checks:
            if path.exists():
                log(f"  [OK] {desc}")
            else:
                log(f"  [FAIL] {desc}: {path}", "ERROR")
                errors.append(desc)

        # Test Python works
        python_exe = hidden_root / "python" / "python.exe"
        if python_exe.exists():
            result = subprocess.run(
                [str(python_exe), "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                log(f"  [OK] Python works: {result.stdout.strip()}")
            else:
                log(f"  [FAIL] Python test failed", "ERROR")
                errors.append("Python test failed")

        unmount_hidden_volume(temp_letter)
    except Exception as e:
        log(f"  Verification error: {e}", "ERROR")
        errors.append(f"Verification error: {e}")

    if errors:
        log(f"\nVerification FAILED with {len(errors)} error(s):", "ERROR")
        for e in errors:
            log(f"  - {e}", "ERROR")
        return False

    log("\nVerification PASSED — all checks OK!")
    return True


# ─── Main ────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="SFFS USB Pack — Automated USB deployment")
    parser.add_argument("--drive", type=str, help="Target drive letter (e.g., E)")
    parser.add_argument("--list", action="store_true", help="List available removable drives")
    parser.add_argument("--skip-build", action="store_true", help="Skip PyInstaller builds (use pre-built)")
    parser.add_argument("--skip-partition", action="store_true", help="Skip partitioning (use existing layout)")
    args = parser.parse_args()

    print("=" * 60)
    print("SFFS USB Pack — Automated USB Deployment")
    print("=" * 60)
    print()

    if args.list:
        drives = list_removable_drives()
        if not drives:
            print("No removable drives found.")
            return 1
        print("Available removable drives:")
        for d in drives:
            print(f"  {d['letter']}:  ({d['total_gb']} GB total, {d['free_gb']} GB free)")
        return 0

    # Step 1: Select drive
    drive_letter = select_drive(target=args.drive)
    print()

    # Step 2: Partition (unless skipped)
    if not args.skip_partition:
        log(f"WARNING: This will WIPE drive {drive_letter}: and repartition it.")
        try:
            confirm = input("Type YES to continue: ").strip()
        except EOFError:
            log("Cannot read input. Use --drive with interactive terminal.", "ERROR")
            return 1
        if confirm != "YES":
            log("Aborted.", "WARN")
            return 1

        visible_drive, hidden_guid = partition_usb(drive_letter)
    else:
        visible_drive = drive_letter
        # Find hidden partition
        hidden_guid = None
        for vol in enumerate_volumes():
            guid = vol if vol.endswith("\\") else vol + "\\"
            from hidden_volume import volume_has_marker, volume_has_no_drive_letter
            if volume_has_no_drive_letter(guid) and volume_has_marker(guid):
                hidden_guid = guid
                break
        if not hidden_guid:
            raise RuntimeError("Hidden partition not found. Run without --skip-partition first.")

    # Step 3: Mount hidden partition for setup
    temp_letter = mount_for_setup(hidden_guid)

    try:
        hidden_root = Path(f"{temp_letter}:\\")

        # Step 4: Create marker file
        create_marker(hidden_root)

        # Step 5: Install Python embeddable
        python_dir = hidden_root / "python"
        python_dir.mkdir(exist_ok=True)
        python_exe = download_python_embeddable(python_dir)
        install_pip(python_exe)
        install_dependencies(python_exe)

        # Step 6: Copy source code
        copy_source_code(hidden_root)

        log("Hidden partition setup complete.")

    finally:
        # Unmount hidden partition
        unmount_for_setup(temp_letter)

    # Step 7: Generate icon
    icon_path = generate_icon()

    # Step 8: Build executables (unless skipped)
    if not args.skip_build:
        launcher_exe, worker_exe = build_executables(icon_path)
    else:
        log("Skipping builds (using pre-built executables).", "WARN")
        launcher_exe = _script_dir / "dist" / "SFFS_launcher.exe"
        worker_exe = _script_dir / "dist" / "SFFS_worker.exe"
        if not launcher_exe.exists() or not worker_exe.exists():
            raise RuntimeError(
                "Pre-built executables not found. Run without --skip-build first."
            )

    # Step 9: Copy to visible partition
    copy_to_visible_partition(visible_drive, launcher_exe, worker_exe)

    # Step 10: Verify
    verify_setup(visible_drive, hidden_guid)

    print()
    print("=" * 60)
    print("USB deployment complete!")
    print("=" * 60)
    print()
    print(f"Visible partition ({visible_drive}:): SFFS_launcher.exe + source code")
    print(f"Hidden partition: Python embeddable + SFFS app + sffs_data/")
    print()
    print("To run SFFS: Double-click SFFS_launcher.exe on the USB.")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
