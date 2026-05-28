#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SFFS USB Installer — One-Click Setup
=====================================
Double-click to install SFFS (Smart File Fortify System) onto a USB drive.
No Python required on the host machine when compiled with PyInstaller.

Supports two modes:
  1. Bundled .exe  — source code embedded via PyInstaller datas
  2. Source mode   — run directly from the project directory

Usage:
    python sffs_usb_installer.py          # GUI installer
    python sffs_usb_installer.py --headless E:   # headless, install to E:
"""

from __future__ import annotations

import ctypes
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

# ── third-party GUI (tkinter is stdlib) ──────────────────────────────────────
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

# ─── Constants ────────────────────────────────────────────────────────────────

VERSION = "1.0.0"
APP_TITLE = "SFFS — Smart File Fortify System  |  USB Installer"

PYTHON_VERSION = "3.13.5"
PYTHON_EMBED_URL = (
    f"https://www.python.org/ftp/python/{PYTHON_VERSION}/"
    f"python-{PYTHON_VERSION}-embed-amd64.zip"
)
PYTHON_EMBED_FALLBACK = "https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

# UI colours
C_BG       = "#0d1117"
C_SURFACE  = "#161b22"
C_BORDER   = "#30363d"
C_ACCENT   = "#1d6ae5"
C_GOLD     = "#f0c060"
C_GREEN    = "#3fb950"
C_RED      = "#f85149"
C_WHITE    = "#e6edf3"
C_MUTED    = "#8b949e"
C_PROG_BG  = "#21262d"

WIN_W, WIN_H = 680, 520

# ─── Locate source root ───────────────────────────────────────────────────────

def _find_source_root() -> Path:
    """Return SFFS project root (contains code1/, code2/, code3/, main-code/)."""
    # When compiled with PyInstaller, source data is at sys._MEIPASS/sffs_src
    if getattr(sys, "frozen", False):
        mei = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        candidate = mei / "sffs_src"
        if candidate.is_dir():
            return candidate
    # Running from source: walk up until we find main-code/
    here = Path(__file__).resolve()
    for parent in [here.parent, here.parent.parent]:
        if (parent / "main-code").is_dir():
            return parent
    raise RuntimeError(
        "Cannot find SFFS source. Run from the project directory or use compiled .exe."
    )


SOURCE_ROOT: Path | None = None  # resolved at runtime after admin check


# ─── Utilities ────────────────────────────────────────────────────────────────

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate_admin() -> None:
    """Re-launch this process with UAC elevation."""
    exe = sys.executable
    script = os.path.abspath(sys.argv[0])
    args = " ".join(f'"{a}"' for a in sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, f'"{script}" {args}', None, 1)
    sys.exit(0)


def list_removable_drives() -> list[dict]:
    """Return list of removable drives with label and size."""
    drives = []
    try:
        import string
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive = f"{letter}:\\"
                dtype = ctypes.windll.kernel32.GetDriveTypeW(drive)
                # DRIVE_REMOVABLE = 2
                if dtype == 2:
                    free = ctypes.c_ulonglong(0)
                    total = ctypes.c_ulonglong(0)
                    avail = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        drive,
                        ctypes.byref(avail),
                        ctypes.byref(total),
                        ctypes.byref(free),
                    )
                    size_gb = total.value / (1024 ** 3)
                    free_gb = free.value / (1024 ** 3)
                    vol_label = ctypes.create_unicode_buffer(256)
                    ctypes.windll.kernel32.GetVolumeInformationW(
                        drive, vol_label, 256, None, None, None, None, 0
                    )
                    label = vol_label.value or "Removable Disk"
                    drives.append({
                        "letter": letter,
                        "path": drive,
                        "label": label,
                        "size_gb": size_gb,
                        "free_gb": free_gb,
                    })
            bitmask >>= 1
    except Exception as e:
        pass
    return drives


def _run(cmd: list[str], timeout: int = 300, cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd
    )


# ─── Core Installation Logic ──────────────────────────────────────────────────

class Installer:
    """Performs installation steps; reports progress via callbacks."""

    def __init__(
        self,
        target_drive: str,          # e.g. "E"
        source_root: Path,
        log_cb: Callable[[str, str], None],   # log_cb(message, level)
        progress_cb: Callable[[int, int], None],  # progress_cb(current, total)
    ):
        self.drive = target_drive.rstrip(":\\") + ":\\"
        self.drive_letter = target_drive.rstrip(":\\")
        self.source_root = source_root
        self.log = log_cb
        self.set_progress = progress_cb
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    # ── Steps ────────────────────────────────────────────────────────────────

    def run(self) -> bool:
        steps = [
            ("Checking drive space",        self._check_space),
            ("Creating directory structure", self._create_dirs),
            ("Copying SFFS source code",    self._copy_source),
            ("Downloading Python runtime",  self._get_python),
            ("Installing pip",              self._install_pip),
            ("Installing dependencies",     self._install_deps),
            ("Creating launcher scripts",   self._create_launchers),
            ("Writing autorun.inf",         self._write_autorun),
            ("Verifying installation",      self._verify),
        ]
        total = len(steps)
        for i, (name, func) in enumerate(steps):
            if self._cancelled:
                self.log("Installation cancelled.", "WARN")
                return False
            self.log(f"[{i+1}/{total}] {name}…", "STEP")
            self.set_progress(i, total)
            try:
                func()
            except Exception as exc:
                self.log(f"FAILED: {exc}", "ERROR")
                return False
        self.set_progress(total, total)
        return True

    def _check_space(self) -> None:
        free = ctypes.c_ulonglong(0)
        total = ctypes.c_ulonglong(0)
        avail = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            self.drive,
            ctypes.byref(avail),
            ctypes.byref(total),
            ctypes.byref(free),
        )
        free_gb = free.value / (1024 ** 3)
        self.log(f"  Free space: {free_gb:.2f} GB", "INFO")
        if free_gb < 0.8:
            raise RuntimeError(f"Not enough free space: {free_gb:.2f} GB (need ≥ 0.8 GB)")

    def _create_dirs(self) -> None:
        for d in ["sffs_data/keys", "sffs_data/logs", "sffs_data/config",
                  "sffs_data/sandbox", "sffs_data/backups",
                  "python", "code1", "code2", "code3", "main-code"]:
            Path(self.drive, d).mkdir(parents=True, exist_ok=True)
        self.log("  Directory structure created.", "OK")

    def _copy_source(self) -> None:
        for dirname in ["code1", "code2", "code3", "main-code", "tests", "docs"]:
            src = self.source_root / dirname
            dst = Path(self.drive) / dirname
            if not src.exists():
                self.log(f"  Skipping missing: {dirname}/", "WARN")
                continue
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                "__pycache__", "*.pyc", "test_output", ".git", "*.egg-info"
            ))
            self.log(f"  Copied {dirname}/", "OK")

        # Also copy apps/ if present (7zip, imageglass)
        apps_src = self.source_root / "apps"
        if apps_src.exists():
            apps_dst = Path(self.drive) / "apps"
            if apps_dst.exists():
                shutil.rmtree(apps_dst)
            shutil.copytree(apps_src, apps_dst)
            self.log("  Copied apps/", "OK")

        # Copy security/ configs (no secrets, just templates)
        sec_src = self.source_root / "security"
        if sec_src.exists():
            sec_dst = Path(self.drive) / "security"
            if sec_dst.exists():
                shutil.rmtree(sec_dst)
            shutil.copytree(sec_src, sec_dst, ignore=shutil.ignore_patterns(
                "*.key", "*.pem", "*.p12"
            ))
            self.log("  Copied security/ (keys excluded)", "OK")

    def _get_python(self) -> None:
        py_dir = Path(self.drive) / "python"
        py_exe = py_dir / "python.exe"
        if py_exe.exists():
            self.log("  Python already present, skipping download.", "OK")
            return
        zip_path = py_dir / "python_embed.zip"
        self.log(f"  Downloading Python {PYTHON_VERSION} embeddable…", "INFO")
        try:
            urllib.request.urlretrieve(PYTHON_EMBED_URL, zip_path,
                                       reporthook=self._dl_hook)
        except Exception:
            self.log("  Primary URL failed, trying fallback…", "WARN")
            try:
                urllib.request.urlretrieve(PYTHON_EMBED_FALLBACK, zip_path,
                                           reporthook=self._dl_hook)
            except Exception as e2:
                raise RuntimeError(
                    f"Python download failed: {e2}\n"
                    "Tip: Run on a machine with internet access."
                ) from e2
        self.log("  Extracting Python…", "INFO")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(py_dir)
        zip_path.unlink(missing_ok=True)
        if not py_exe.exists():
            raise RuntimeError("python.exe not found after extraction.")
        self.log(f"  Python installed at {py_exe}", "OK")

    def _dl_hook(self, block: int, block_size: int, total: int) -> None:
        if total > 0:
            done = block * block_size
            pct = min(100, int(done * 100 / total))
            if pct % 10 == 0:
                self.log(f"    … {pct}% ({done/1024/1024:.1f} MB / {total/1024/1024:.1f} MB)", "INFO")

    def _install_pip(self) -> None:
        py_exe = Path(self.drive) / "python" / "python.exe"
        # Enable site-packages for embeddable python
        for pth in py_exe.parent.glob("python*._pth"):
            content = pth.read_text(encoding="utf-8")
            if "import site" not in content:
                pth.write_text(content + "\nimport site\n", encoding="utf-8")
                self.log("  Enabled site-packages in ._pth", "INFO")

        pip_check = _run([str(py_exe), "-m", "pip", "--version"])
        if pip_check.returncode == 0:
            self.log("  pip already present.", "OK")
            return
        self.log("  Downloading get-pip.py…", "INFO")
        get_pip = py_exe.parent / "get-pip.py"
        urllib.request.urlretrieve(GET_PIP_URL, get_pip)
        result = _run([str(py_exe), str(get_pip)], timeout=120)
        get_pip.unlink(missing_ok=True)
        if result.returncode != 0:
            raise RuntimeError(f"pip install failed: {result.stderr[:300]}")
        self.log("  pip installed.", "OK")

    def _install_deps(self) -> None:
        py_exe = Path(self.drive) / "python" / "python.exe"
        req = Path(self.drive) / "main-code" / "requirements.txt"
        if not req.exists():
            self.log("  requirements.txt not found, skipping.", "WARN")
            return
        self.log("  Installing Python dependencies (may take 3-5 min)…", "INFO")
        result = _run(
            [str(py_exe), "-m", "pip", "install", "-r", str(req),
             "--no-warn-script-location"],
            timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"pip install -r requirements.txt failed:\n{result.stderr[:500]}")
        self.log("  All dependencies installed.", "OK")

    def _create_launchers(self) -> None:
        drive = Path(self.drive)

        # ── RUN_SFFS.bat (Windows) ──────────────────────────────────────────
        bat = (
            "@echo off\r\n"
            "title SFFS - Smart File Fortify System\r\n"
            "cd /d \"%~dp0\"\r\n"
            "set PYTHONPATH=%~dp0code1;%~dp0code2;%~dp0code3;%~dp0main-code\r\n"
            "if exist python\\python.exe (\r\n"
            "    python\\python.exe main-code\\main.py %*\r\n"
            ") else (\r\n"
            "    python main-code\\main.py %*\r\n"
            ")\r\n"
            "if errorlevel 1 pause\r\n"
        )
        (drive / "RUN_SFFS.bat").write_text(bat, encoding="utf-8")
        self.log("  Created RUN_SFFS.bat", "OK")

        # ── RUN_SFFS_HEADLESS.bat ───────────────────────────────────────────
        bat_headless = (
            "@echo off\r\n"
            "title SFFS CLI\r\n"
            "cd /d \"%~dp0\"\r\n"
            "set PYTHONPATH=%~dp0code1;%~dp0code2;%~dp0code3;%~dp0main-code\r\n"
            "if exist python\\python.exe (\r\n"
            "    python\\python.exe main-code\\main.py --headless %*\r\n"
            ") else (\r\n"
            "    python main-code\\main.py --headless %*\r\n"
            ")\r\n"
            "pause\r\n"
        )
        (drive / "RUN_SFFS_HEADLESS.bat").write_text(bat_headless, encoding="utf-8")
        self.log("  Created RUN_SFFS_HEADLESS.bat", "OK")

        # ── run_sffs.sh (Linux fallback) ─────────────────────────────────────
        sh = (
            "#!/usr/bin/env bash\n"
            "set -e\n"
            "SCRIPT_DIR=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
            "cd \"$SCRIPT_DIR\"\n"
            "export PYTHONPATH=\"$SCRIPT_DIR/code1:$SCRIPT_DIR/code2:"
            "$SCRIPT_DIR/code3:$SCRIPT_DIR/main-code\"\n"
            "python3 main-code/main.py \"$@\"\n"
        )
        sh_file = drive / "run_sffs.sh"
        sh_file.write_text(sh, encoding="utf-8")
        try:
            sh_file.chmod(0o755)
        except Exception:
            pass
        self.log("  Created run_sffs.sh (Linux)", "OK")

        # ── README.txt ───────────────────────────────────────────────────────
        readme = (
            "SFFS — Smart File Fortify System\n"
            "=" * 40 + "\n\n"
            "WINDOWS:\n"
            "  Double-click  RUN_SFFS.bat  to launch the GUI.\n"
            "  Double-click  RUN_SFFS_HEADLESS.bat  for CLI demo.\n\n"
            "LINUX / macOS:\n"
            "  bash run_sffs.sh\n"
            "  (Install deps first: pip install -r main-code/requirements.txt)\n\n"
            "REQUIREMENTS (for host Python path):\n"
            "  Python 3.11+, PyQt6, pycryptodome, cryptography, argon2-cffi\n\n"
            f"Installed by SFFS USB Installer v{VERSION} on {time.strftime('%Y-%m-%d %H:%M')}\n"
        )
        (drive / "README.txt").write_text(readme, encoding="utf-8")
        self.log("  Created README.txt", "OK")

        # ── Copy pre-built SFFS_launcher.exe if available ───────────────────
        for exe_name in ("SFFS_launcher.exe", "SFFS_worker.exe"):
            for candidate in [
                self.source_root / "scripts" / "usb-pack" / "dist" / exe_name,
                self.source_root.parent / "scripts" / "usb-pack" / "dist" / exe_name,
            ]:
                if candidate.exists():
                    shutil.copy2(candidate, drive / exe_name)
                    self.log(f"  Copied {exe_name}", "OK")
                    break

    def _write_autorun(self) -> None:
        content = (
            "[AutoRun]\r\n"
            "open=RUN_SFFS.bat\r\n"
            "action=Launch SFFS\r\n"
            "label=SFFS - Smart File Fortify System\r\n"
            "icon=SFFS_launcher.exe,0\r\n"
        )
        (Path(self.drive) / "autorun.inf").write_text(content, encoding="utf-8")
        self.log("  Created autorun.inf", "OK")

    def _verify(self) -> None:
        checks = [
            Path(self.drive) / "main-code" / "main.py",
            Path(self.drive) / "main-code" / "requirements.txt",
            Path(self.drive) / "code1" / "f01_generate_key_pairs.py",
            Path(self.drive) / "code2" / "f07_create_isolated_sandbox.py",
            Path(self.drive) / "code3" / "f13_init_drive_detection.py",
            Path(self.drive) / "python" / "python.exe",
            Path(self.drive) / "RUN_SFFS.bat",
        ]
        failed = [str(c) for c in checks if not c.exists()]
        if failed:
            raise RuntimeError(
                "Verification failed — missing:\n" + "\n".join(f"  {f}" for f in failed)
            )
        self.log("  All critical files verified.", "OK")


# ─── GUI ──────────────────────────────────────────────────────────────────────

class InstallerApp(tk.Tk):
    """Multi-step GUI installer."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.resizable(False, False)
        self.configure(bg=C_BG)

        self._set_icon()
        self._load_fonts()
        self._build_ui()
        self._show_step(0)

        # State
        self._installer: Installer | None = None
        self._log_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self._install_thread: threading.Thread | None = None

    # ── Icon & fonts ─────────────────────────────────────────────────────────

    def _set_icon(self) -> None:
        """Try to set window icon from sffs.ico if bundled."""
        for ico_path in [
            Path(__file__).parent / "usb-pack" / "sffs.ico",
            Path(__file__).parent / "sffs.ico",
        ]:
            if ico_path.exists():
                try:
                    self.iconbitmap(str(ico_path))
                    return
                except Exception:
                    pass

    def _load_fonts(self) -> None:
        self.f_title  = tkfont.Font(family="Segoe UI", size=18, weight="bold")
        self.f_sub    = tkfont.Font(family="Segoe UI", size=10)
        self.f_body   = tkfont.Font(family="Segoe UI", size=10)
        self.f_btn    = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.f_mono   = tkfont.Font(family="Consolas",  size=9)
        self.f_label  = tkfont.Font(family="Segoe UI", size=9)

    # ── Layout shell ─────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Header bar
        hdr = tk.Frame(self, bg=C_SURFACE, height=64)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Label(
            hdr, text="🛡  SFFS USB Installer", font=self.f_title,
            bg=C_SURFACE, fg=C_WHITE, padx=20
        ).pack(side="left", pady=12)
        tk.Label(
            hdr, text=f"v{VERSION}", font=self.f_sub,
            bg=C_SURFACE, fg=C_MUTED, padx=10
        ).pack(side="right", pady=12)

        # Step indicator
        self._step_bar = tk.Frame(self, bg=C_BORDER, height=3)
        self._step_bar.pack(fill="x")

        self._step_fill = tk.Frame(self._step_bar, bg=C_ACCENT, height=3)
        self._step_fill.place(x=0, y=0, width=0, height=3)

        # Main content area
        self._content = tk.Frame(self, bg=C_BG)
        self._content.pack(fill="both", expand=True, padx=30, pady=16)

        # Bottom button bar
        self._btn_bar = tk.Frame(self, bg=C_SURFACE, height=56)
        self._btn_bar.pack(fill="x", side="bottom")
        self._btn_bar.pack_propagate(False)

        self._btn_back = tk.Button(
            self._btn_bar, text="◀  Back", font=self.f_btn,
            bg=C_SURFACE, fg=C_MUTED, bd=0, padx=20,
            activebackground=C_BORDER, activeforeground=C_WHITE,
            command=self._go_back,
        )
        self._btn_back.pack(side="left", padx=20, pady=10)

        self._btn_next = tk.Button(
            self._btn_bar, text="Next  ▶", font=self.f_btn,
            bg=C_ACCENT, fg=C_WHITE, bd=0, padx=24,
            activebackground="#2d7de8", activeforeground=C_WHITE,
            cursor="hand2",
            command=self._go_next,
        )
        self._btn_next.pack(side="right", padx=20, pady=10)

        # Steps: 0=welcome 1=drive 2=progress 3=done
        self._step = 0
        self._frames: list[tk.Frame] = [
            self._build_welcome(),
            self._build_drive_select(),
            self._build_progress(),
            self._build_done(),
        ]

    def _show_step(self, step: int) -> None:
        self._step = step
        for i, f in enumerate(self._frames):
            f.pack_forget()
        self._frames[step].pack(fill="both", expand=True)

        # Update step bar width
        fill_w = int((step / 3) * WIN_W)
        self._step_fill.place(x=0, y=0, width=fill_w, height=3)

        # Button visibility
        self._btn_back.configure(state="normal" if 0 < step < 2 else "disabled",
                                  fg=C_MUTED if step == 0 else C_WHITE)
        if step == 0:
            self._btn_next.configure(text="Get Started  ▶", bg=C_ACCENT, state="normal")
        elif step == 1:
            self._btn_next.configure(text="Install  ▶", bg=C_ACCENT, state="normal")
        elif step == 2:
            self._btn_next.configure(text="Installing…", bg=C_BORDER, state="disabled")
        elif step == 3:
            self._btn_next.configure(text="Close", bg=C_GREEN, state="normal",
                                      command=self.destroy)
            self._btn_back.configure(state="disabled")

    def _go_next(self) -> None:
        if self._step == 0:
            self._show_step(1)
            self._refresh_drives()
        elif self._step == 1:
            self._start_install()
        elif self._step == 3:
            self.destroy()

    def _go_back(self) -> None:
        if self._step == 1:
            self._show_step(0)

    # ── Step 0: Welcome ───────────────────────────────────────────────────────

    def _build_welcome(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=C_BG)

        tk.Label(
            f, text="Welcome to SFFS USB Installer",
            font=tkfont.Font(family="Segoe UI", size=15, weight="bold"),
            bg=C_BG, fg=C_WHITE,
        ).pack(pady=(10, 6))

        tk.Label(
            f,
            text=(
                "This wizard will install the Smart File Fortify System onto\n"
                "your USB drive — including Python runtime and all dependencies.\n\n"
                "You will need:\n"
                "  •  A USB drive with ≥ 1 GB free space\n"
                "  •  An internet connection (for Python & packages)\n"
                "  •  Administrator privileges (auto-requested)\n\n"
                "After installation, run  RUN_SFFS.bat  from the USB to launch SFFS."
            ),
            font=self.f_body, bg=C_BG, fg=C_WHITE, justify="left",
        ).pack(padx=20, pady=8)

        # Info box
        info = tk.Frame(f, bg=C_SURFACE, relief="flat", bd=0)
        info.pack(fill="x", padx=10, pady=10)
        tk.Label(
            info,
            text=(
                "ℹ️  Existing SFFS data on the USB will be overwritten.\n"
                "    sffs_data/ folder (keys, logs) will NOT be deleted."
            ),
            font=self.f_label, bg=C_SURFACE, fg=C_GOLD, justify="left",
            padx=14, pady=10,
        ).pack(fill="x")

        return f

    # ── Step 1: Drive select ──────────────────────────────────────────────────

    def _build_drive_select(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=C_BG)

        tk.Label(
            f, text="Select USB Drive",
            font=tkfont.Font(family="Segoe UI", size=13, weight="bold"),
            bg=C_BG, fg=C_WHITE,
        ).pack(pady=(6, 4))

        tk.Label(
            f,
            text="Choose the USB drive to install SFFS on. Only removable drives are shown.",
            font=self.f_body, bg=C_BG, fg=C_MUTED,
        ).pack(pady=(0, 10))

        # Drive list frame
        list_frame = tk.Frame(f, bg=C_SURFACE, relief="flat")
        list_frame.pack(fill="x", padx=6)

        self._drive_var = tk.StringVar(value="")
        self._drive_btns: list[tk.Radiobutton] = []
        self._drive_list_frame = list_frame

        # Refresh button
        ref_row = tk.Frame(f, bg=C_BG)
        ref_row.pack(fill="x", padx=6, pady=6)
        tk.Button(
            ref_row, text="🔄  Refresh Drive List", font=self.f_btn,
            bg=C_BORDER, fg=C_WHITE, bd=0, padx=12, pady=4,
            activebackground=C_ACCENT, activeforeground=C_WHITE,
            cursor="hand2",
            command=self._refresh_drives,
        ).pack(side="left")

        self._drive_hint = tk.Label(
            f, text="", font=self.f_label, bg=C_BG, fg=C_MUTED
        )
        self._drive_hint.pack(pady=4)

        return f

    def _refresh_drives(self) -> None:
        for w in self._drive_list_frame.winfo_children():
            w.destroy()
        self._drive_btns.clear()
        drives = list_removable_drives()
        if not drives:
            tk.Label(
                self._drive_list_frame,
                text="  No removable drives found. Insert a USB and click Refresh.",
                font=self.f_body, bg=C_SURFACE, fg=C_RED, padx=14, pady=14,
            ).pack(fill="x")
            self._btn_next.configure(state="disabled")
            return

        self._drive_var.set(drives[0]["letter"])
        for d in drives:
            row = tk.Frame(self._drive_list_frame, bg=C_SURFACE)
            row.pack(fill="x", padx=2, pady=1)
            rb = tk.Radiobutton(
                row,
                text=(
                    f"  {d['letter']}:   {d['label']}   "
                    f"({d['size_gb']:.1f} GB total, {d['free_gb']:.1f} GB free)"
                ),
                variable=self._drive_var, value=d["letter"],
                font=self.f_body, bg=C_SURFACE, fg=C_WHITE,
                selectcolor=C_ACCENT, activebackground=C_SURFACE,
                activeforeground=C_WHITE, bd=0,
            )
            rb.pack(side="left", padx=10, pady=8)
            self._drive_btns.append(rb)

        self._btn_next.configure(state="normal")
        self._drive_hint.configure(
            text=f"  {len(drives)} removable drive(s) detected.",
            fg=C_GREEN,
        )

    # ── Step 2: Progress ──────────────────────────────────────────────────────

    def _build_progress(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=C_BG)

        tk.Label(
            f, text="Installing SFFS…",
            font=tkfont.Font(family="Segoe UI", size=13, weight="bold"),
            bg=C_BG, fg=C_WHITE,
        ).pack(pady=(6, 4))

        self._prog_label = tk.Label(
            f, text="Preparing…", font=self.f_body, bg=C_BG, fg=C_MUTED
        )
        self._prog_label.pack(pady=2)

        # Progress bar
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure(
            "SFFS.Horizontal.TProgressbar",
            troughcolor=C_PROG_BG, background=C_ACCENT,
            bordercolor=C_BORDER, lightcolor=C_ACCENT, darkcolor=C_ACCENT,
        )
        self._progress = ttk.Progressbar(
            f, style="SFFS.Horizontal.TProgressbar",
            length=580, mode="determinate", maximum=100,
        )
        self._progress.pack(pady=8)

        # Log area
        log_frame = tk.Frame(f, bg=C_SURFACE)
        log_frame.pack(fill="both", expand=True, pady=4)
        self._log_text = tk.Text(
            log_frame, bg=C_SURFACE, fg=C_WHITE, font=self.f_mono,
            bd=0, relief="flat", wrap="word", state="disabled",
            height=14,
        )
        sb = tk.Scrollbar(log_frame, command=self._log_text.yview, bg=C_BORDER, bd=0)
        self._log_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log_text.pack(fill="both", expand=True, padx=6, pady=6)

        # Tag colours
        self._log_text.tag_configure("STEP",  foreground=C_GOLD)
        self._log_text.tag_configure("OK",    foreground=C_GREEN)
        self._log_text.tag_configure("WARN",  foreground=C_GOLD)
        self._log_text.tag_configure("ERROR", foreground=C_RED)
        self._log_text.tag_configure("INFO",  foreground=C_MUTED)

        return f

    def _append_log(self, msg: str, level: str = "INFO") -> None:
        self._log_text.configure(state="normal")
        self._log_text.insert("end", msg + "\n", level)
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _update_progress(self, current: int, total: int) -> None:
        pct = int(current * 100 / total) if total else 0
        self._progress["value"] = pct
        self._prog_label.configure(text=f"Step {current} of {total}  ({pct}%)")

    # ── Step 3: Done ─────────────────────────────────────────────────────────

    def _build_done(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=C_BG)
        self._done_icon = tk.Label(f, text="", font=tkfont.Font(family="Segoe UI", size=48),
                                    bg=C_BG)
        self._done_icon.pack(pady=(20, 6))
        self._done_title = tk.Label(f, text="", font=self.f_title, bg=C_BG, fg=C_WHITE)
        self._done_title.pack()
        self._done_body = tk.Label(f, text="", font=self.f_body, bg=C_BG, fg=C_MUTED,
                                    justify="center")
        self._done_body.pack(pady=10)
        return f

    def _show_done(self, success: bool, drive_letter: str = "") -> None:
        if success:
            self._done_icon.configure(text="✅", fg=C_GREEN)
            self._done_title.configure(text="Installation Complete!", fg=C_GREEN)
            self._done_body.configure(
                text=(
                    f"SFFS has been installed on drive {drive_letter}:\n\n"
                    f"  ▶  Double-click  RUN_SFFS.bat  to launch\n"
                    f"  ▶  Python runtime embedded — no install needed on other PCs\n\n"
                    "You can safely eject the USB drive."
                ),
                fg=C_WHITE,
            )
        else:
            self._done_icon.configure(text="❌", fg=C_RED)
            self._done_title.configure(text="Installation Failed", fg=C_RED)
            self._done_body.configure(
                text=(
                    "Installation did not complete successfully.\n"
                    "Check the log in the previous step for details.\n\n"
                    "Common fixes:\n"
                    "  •  Ensure internet connection for Python download\n"
                    "  •  Make sure USB has ≥ 1 GB free\n"
                    "  •  Run as Administrator"
                ),
                fg=C_MUTED,
            )
        self._show_step(3)

    # ── Install orchestration ─────────────────────────────────────────────────

    def _start_install(self) -> None:
        drive_letter = self._drive_var.get()
        if not drive_letter:
            messagebox.showerror("No Drive", "Please select a USB drive.")
            return

        drives = list_removable_drives()
        chosen = next((d for d in drives if d["letter"] == drive_letter), None)
        if not chosen:
            messagebox.showerror("Drive Not Found",
                                  f"Drive {drive_letter}: not found. Refresh and try again.")
            return

        confirm = messagebox.askyesno(
            "Confirm Installation",
            f"Install SFFS on  {drive_letter}:  ({chosen['label']})?\n\n"
            "Source code will be overwritten.\n"
            "sffs_data/ (keys/logs) will NOT be deleted.",
        )
        if not confirm:
            return

        try:
            source = _find_source_root()
        except RuntimeError as e:
            messagebox.showerror("Source Not Found", str(e))
            return

        self._show_step(2)

        def _log(msg: str, level: str = "INFO") -> None:
            self._log_queue.put((msg, level))

        def _prog(cur: int, tot: int) -> None:
            self.after(0, self._update_progress, cur, tot)

        self._installer = Installer(
            target_drive=drive_letter,
            source_root=source,
            log_cb=_log,
            progress_cb=_prog,
        )

        def _worker() -> None:
            success = self._installer.run()  # type: ignore[union-attr]
            self.after(0, self._show_done, success, drive_letter)

        self._install_thread = threading.Thread(target=_worker, daemon=True)
        self._install_thread.start()
        self._drain_log_queue()

    def _drain_log_queue(self) -> None:
        try:
            while True:
                msg, level = self._log_queue.get_nowait()
                self._append_log(msg, level)
        except queue.Empty:
            pass
        if self._install_thread and self._install_thread.is_alive():
            self.after(100, self._drain_log_queue)


# ─── Headless mode ────────────────────────────────────────────────────────────

def headless_install(drive_letter: str) -> int:
    """Run installation without GUI. Returns exit code."""
    source = _find_source_root()
    print(f"Source root: {source}")
    print(f"Target drive: {drive_letter}:")

    def log(msg: str, level: str = "INFO") -> None:
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] [{level}] {msg}")

    def prog(cur: int, tot: int) -> None:
        print(f"  Progress: {cur}/{tot}")

    installer = Installer(
        target_drive=drive_letter,
        source_root=source,
        log_cb=log,
        progress_cb=prog,
    )
    ok = installer.run()
    print()
    print("=" * 50)
    print("SUCCESS" if ok else "FAILED")
    print("=" * 50)
    return 0 if ok else 1


# ─── Entry point ──────────────────────────────────────────────────────────────

def main() -> int:
    # Auto-elevate if not admin
    if not is_admin():
        print("Requesting administrator privileges…")
        elevate_admin()
        return 0

    # Headless mode: python sffs_usb_installer.py --headless E
    if len(sys.argv) >= 3 and sys.argv[1] == "--headless":
        return headless_install(sys.argv[2])

    app = InstallerApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
