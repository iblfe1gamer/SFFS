"""
setup_usb_standalone.py — Run this directly on a USB to set up SFFS.

Double-click this file (or run: python setup_usb_standalone.py) on a USB drive
to automatically:
  1. Partition the USB into visible + hidden NTFS partitions
  2. Download Python 3.14.3 embeddable to the hidden partition
  3. Install all SFFS dependencies
  4. Copy source code to both partitions
  5. Build PyInstaller executables
  6. Set up autorun.inf and README

Requires: Administrator privileges, Python 3.10+, internet connection.
"""

from __future__ import annotations

import ctypes
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

HIDDEN_SIZE_MB = 2048  # 2 GB hidden partition
DRIVE_LETTER_MOUNT = "S"  # Temporary mount letter


def log(msg: str, level: str = "INFO") -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def run_cmd(cmd: list[str], check: bool = True, timeout: int = 300) -> subprocess.CompletedProcess:
    log(f"  > {' '.join(cmd[:4])}{'...' if len(cmd) > 4 else ''}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.stdout.strip():
        for line in result.stdout.strip().split("\n")[-3:]:
            log(f"    {line}")
    if result.stderr.strip():
        for line in result.stderr.strip().split("\n")[-3:]:
            log(f"    [stderr] {line}", "WARN")
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed (rc={result.returncode}): {cmd[0]}")
    return result


def run_diskpart(script: str) -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(script)
        f.flush()
        temp_path = f.name
    try:
        run_cmd(["diskpart", "/s", temp_path], timeout=120)
    finally:
        os.unlink(temp_path)


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_as_admin() -> None:
    """Relaunch this script with admin privileges."""
    exe = sys.executable
    script = sys.argv[0]
    args = sys.argv[1:]
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", exe, f'"{script}" {" ".join(args)}', None, 1
    )
    sys.exit(0)


def get_current_drive() -> str:
    """Get the drive letter where this script is running."""
    return Path(__file__).resolve().anchor.rstrip("\\")


def get_usb_size(drive_letter: str) -> float:
    """Get USB total size in GB."""
    import ctypes
    free_bytes = ctypes.c_ulonglong(0)
    total_bytes = ctypes.c_ulonglong(0)
    avail_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
        f"{drive_letter}:\\",
        ctypes.byref(free_bytes),
        ctypes.byref(total_bytes),
        ctypes.byref(avail_bytes),
    )
    return total_bytes.value / (1024**3)


def get_disk_number(drive_letter: str) -> int:
    result = run_cmd(
        ["powershell", "-Command",
         f"(Get-Partition -DriveLetter '{drive_letter}').DiskNumber"],
    )
    return int(result.stdout.strip())


def partition_usb(drive_letter: str) -> str:
    """Wipe and repartition the USB. Returns the hidden partition's volume GUID."""
    log(f"Partitioning drive {drive_letter}: ...")
    disk_num = get_disk_number(drive_letter)
    log(f"Drive {drive_letter}: is on disk {disk_num}")

    diskpart_script = f"""
select disk {disk_num}
clean
convert gpt
create partition primary size=200
format quick fs=ntfs label="SFFS"
assign letter={drive_letter}
create partition primary size={HIDDEN_SIZE_MB}
format quick fs=ntfs label="SFFS_DATA"
remove
exit
"""
    run_diskpart(diskpart_script)
    log(f"Partitioned: 200MB visible + {HIDDEN_SIZE_MB}MB hidden")

    # Find hidden partition volume GUID
    result = run_cmd(
        ["powershell", "-Command",
         f"Get-Partition -DiskNumber {disk_num} | Where-Object {{ $_.DriveLetter -eq $null }} | Get-Volume | Select-Object -ExpandProperty ObjectId"],
    )
    output = result.stdout.strip()
    if output and "Volume{" in output:
        start = output.index("\\\\?\\")
        end = output.index("\\", start + 4) + 1
        return output[start:end]
    raise RuntimeError("Could not find hidden partition volume GUID.")


def mount_volume(volume_guid: str, letter: str = "X") -> bool:
    """Mount a volume to a drive letter."""
    try:
        result = ctypes.windll.kernel32.DefineDosDeviceW(
            0x00000001,  # DDD_RAW_TARGET_PATH
            f"{letter}:",
            volume_guid,
        )
        return result != 0
    except Exception:
        try:
            run_cmd(["mountvol", f"{letter}:", volume_guid])
            return True
        except Exception:
            return False


def unmount_volume(letter: str = "X") -> None:
    """Unmount a drive letter."""
    try:
        ctypes.windll.kernel32.DefineDosDeviceW(
            0x00000002 | 0x00000004,  # DDD_REMOVE_DEFINITION | DDD_EXACT_MATCH_ON_REMOVE
            f"{letter}:",
            None,
        )
    except Exception:
        try:
            run_cmd(["mountvol", f"{letter}:", "/d"])
        except Exception:
            pass


def download_python_embeddable(target_dir: Path) -> Path:
    log(f"Downloading Python {PYTHON_VERSION} embeddable...")
    zip_path = target_dir / "python_embed.zip"
    try:
        urllib.request.urlretrieve(PYTHON_EMBED_URL, zip_path)
    except Exception:
        log("Primary download failed, trying fallback...", "WARN")
        urllib.request.urlretrieve(PYTHON_EMBED_FALLBACK_URL, zip_path)

    log("Extracting Python embeddable...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target_dir)
    zip_path.unlink()

    python_exe = target_dir / "python.exe"
    if not python_exe.exists():
        for p in target_dir.rglob("python.exe"):
            python_exe = p
            break
    if not python_exe.exists():
        raise RuntimeError("python.exe not found after extraction.")
    return python_exe


def install_pip(python_exe: Path) -> None:
    log("Installing pip...")
    get_pip_path = python_exe.parent / "get-pip.py"
    urllib.request.urlretrieve(GET_PIP_URL, get_pip_path)

    # Enable site-packages
    for pth in python_exe.parent.glob("python*._pth"):
        content = pth.read_text(encoding="utf-8")
        if "import site" not in content:
            content += "\nimport site\n"
            pth.write_text(content, encoding="utf-8")

    run_cmd([str(python_exe), str(get_pip_path)])
    get_pip_path.unlink()
    log("pip installed.")


def install_dependencies(python_exe: Path, requirements_file: Path) -> None:
    log("Installing SFFS dependencies...")
    run_cmd([str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)])
    log("Dependencies installed.")


def copy_source_code(hidden_root: Path, source_root: Path) -> None:
    log("Copying SFFS source code...")
    for dirname in ["code1", "code2", "code3", "main-code"]:
        src = source_root / dirname
        dst = hidden_root / dirname
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            for p in list(dst.rglob("__pycache__")) + list(dst.rglob("test_output")):
                if p.is_dir():
                    shutil.rmtree(p)
            log(f"  Copied {dirname}/")


def generate_icon(output_path: Path) -> None:
    """Generate a simple multi-resolution .ico file."""
    log("Generating SFFS icon...")
    try:
        from PIL import Image, ImageDraw
        sizes = [16, 24, 32, 48, 64, 128]
        images = []
        for size in sizes:
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            cx, cy = size / 2, size / 2
            r = int(size * 0.44)
            # Shield hexagon
            import math
            points = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                points.append((int(round(x)), int(round(y))))
            draw.polygon(points, fill=(26, 35, 126))
            draw.polygon(points, outline=(189, 195, 199), width=max(1, size // 32))
            # Lock body
            bw, bh = size * 0.5, size * 0.35
            bx, by = cx - bw / 2, cy - bh / 2 + size * 0.1
            draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=max(2, size // 24), fill=(255, 215, 0))
            images.append(img)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        images[0].save(str(output_path), format="ICO",
                       sizes=[(img.width, img.height) for img in images],
                       append_images=images[1:])
        log(f"Icon saved: {output_path}")
    except ImportError:
        log("Pillow not available, skipping icon generation.", "WARN")


def build_executables(icon_path: Path, script_dir: Path) -> tuple[Path, Path]:
    log("Building executables with PyInstaller...")
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        log("Installing PyInstaller...", "WARN")
        run_cmd([sys.executable, "-m", "pip", "install", "pyinstaller"])

    dist_dir = script_dir / "dist"
    build_dir = script_dir / "build"

    log("Building SFFS_launcher.exe...")
    run_cmd([
        sys.executable, "-m", "PyInstaller",
        str(script_dir / "sffs_bootstrap.spec"),
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--noconfirm",
    ], timeout=600)

    launcher_exe = dist_dir / "SFFS_launcher.exe"
    if not launcher_exe.exists():
        raise RuntimeError(f"Launcher build failed: {launcher_exe}")
    log(f"Launcher: {launcher_exe.name} ({launcher_exe.stat().st_size / 1024 / 1024:.1f} MB)")

    log("Building SFFS_worker.exe...")
    run_cmd([
        sys.executable, "-m", "PyInstaller",
        str(script_dir / "sffs_worker.spec"),
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--noconfirm",
    ], timeout=600)

    worker_exe = dist_dir / "SFFS_worker.exe"
    if not worker_exe.exists():
        raise RuntimeError(f"Worker build failed: {worker_exe}")
    log(f"Worker: {worker_exe.name} ({worker_exe.stat().st_size / 1024 / 1024:.1f} MB)")

    return launcher_exe, worker_exe


def main() -> int:
    print("=" * 60)
    print("SFFS USB Setup — Standalone Installer")
    print("=" * 60)
    print()

    # Check admin
    if not is_admin():
        log("Administrator privileges required. Requesting elevation...", "WARN")
        run_as_admin()
        return 0

    # Get current drive
    drive_letter = get_current_drive()
    usb_size = get_usb_size(drive_letter)
    log(f"Running from drive {drive_letter}: ({usb_size:.1f} GB)")

    # Confirm
    print()
    log(f"WARNING: This will WIPE drive {drive_letter}: and repartition it.")
    log(f"Visible partition: ~{(usb_size - HIDDEN_SIZE_MB / 1024):.1f} GB")
    log(f"Hidden partition: {HIDDEN_SIZE_MB} MB")
    confirm = input("Type YES to continue: ").strip()
    if confirm != "YES":
        log("Aborted.", "WARN")
        return 1

    # Find source root (parent of main-code/)
    script_parent = Path(__file__).resolve().parent
    if (script_parent / "main-code").exists():
        source_root = script_parent
    elif (script_parent.parent / "main-code").exists():
        source_root = script_parent.parent
    else:
        raise RuntimeError("Cannot find SFFS source code. Run this from the SFFS directory.")

    log(f"Source root: {source_root}")

    # Step 1: Partition
    hidden_guid = partition_usb(drive_letter)
    log(f"Hidden partition GUID: {hidden_guid}")

    # Step 2: Mount hidden partition
    temp_letter = "X"
    if not mount_volume(hidden_guid, temp_letter):
        raise RuntimeError(f"Failed to mount hidden partition to {temp_letter}:")
    hidden_root = Path(f"{temp_letter}:\\")
    log(f"Hidden partition mounted at {temp_letter}:\\")

    try:
        # Step 3: Create marker
        (hidden_root / ".sffs_marker").write_text(
            f"SFFS Hidden Partition\nCreated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8",
        )
        log("Created .sffs_marker")

        # Step 4: Install Python embeddable
        python_dir = hidden_root / "python"
        python_dir.mkdir(exist_ok=True)
        python_exe = download_python_embeddable(python_dir)
        install_pip(python_exe)

        # Step 5: Install dependencies
        requirements = source_root / "main-code" / "requirements.txt"
        if requirements.exists():
            install_dependencies(python_exe, requirements)

        # Step 6: Copy source code
        copy_source_code(hidden_root, source_root)

        # Create sffs_data structure
        for subdir in ["keys", "logs", "config", "sandbox", "backups"]:
            (hidden_root / "sffs_data" / subdir).mkdir(parents=True, exist_ok=True)
        log("Created sffs_data/ structure")

    finally:
        unmount_volume(temp_letter)
        log(f"Unmounted {temp_letter}:")

    # Step 7: Generate icon
    icon_path = script_parent / "sffs.ico"
    generate_icon(icon_path)

    # Step 8: Build executables
    launcher_exe, worker_exe = build_executables(icon_path, script_parent)

    # Step 9: Copy to visible partition
    visible_root = Path(f"{drive_letter}:\\")
    shutil.copy2(launcher_exe, visible_root / "SFFS_launcher.exe")
    shutil.copy2(worker_exe, visible_root / "SFFS_worker.exe")
    log("Copied executables to visible partition")

    # Copy source for Linux fallback
    for dirname in ["code1", "code2", "code3", "main-code"]:
        src = source_root / dirname
        dst = visible_root / dirname
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            for p in list(dst.rglob("__pycache__")) + list(dst.rglob("test_output")):
                if p.is_dir():
                    shutil.rmtree(p)
    log("Copied source code to visible partition")

    # Create autorun.inf
    (visible_root / "autorun.inf").write_text(
        "[AutoRun]\n"
        "open=SFFS_launcher.exe\n"
        "action=Run SFFS\n"
        "icon=SFFS_launcher.exe,0\n"
        "label=SFFS - Smart File Fortify System\n",
        encoding="utf-8",
    )
    log("Created autorun.inf")

    # Create README.txt
    (visible_root / "README.txt").write_text(
        "SFFS - Smart File Fortify System\n"
        "=" * 40 + "\n\n"
        "Windows: Double-click SFFS_launcher.exe to run.\n\n"
        "Linux: Copy the source code directories to a local directory,\n"
        "install dependencies (pip install -r main-code/requirements.txt),\n"
        "and run: python main-code/main.py\n",
        encoding="utf-8",
    )
    log("Created README.txt")

    # Step 10: Verify
    log("Verifying setup...")
    temp_letter = "V"
    mount_volume(hidden_guid, temp_letter)
    hidden_root = Path(f"{temp_letter}:\\")
    checks = [
        (hidden_root / ".sffs_marker", "Marker file"),
        (hidden_root / "python" / "python.exe", "Python executable"),
        (hidden_root / "code1", "Code1"),
        (hidden_root / "code2", "Code2"),
        (hidden_root / "code3", "Code3"),
        (hidden_root / "main-code", "Main-code"),
        (hidden_root / "sffs_data", "sffs_data"),
        (visible_root / "SFFS_launcher.exe", "Launcher"),
        (visible_root / "SFFS_worker.exe", "Worker"),
    ]
    all_ok = True
    for path, desc in checks:
        status = "OK" if path.exists() else "FAIL"
        if status == "FAIL":
            all_ok = False
        log(f"  [{status}] {desc}")
    unmount_volume(temp_letter)

    print()
    print("=" * 60)
    if all_ok:
        print("USB setup COMPLETE!")
        print(f"Drive {drive_letter}: is ready. Double-click SFFS_launcher.exe to run.")
    else:
        print("Setup completed with some issues. Check the log above.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
