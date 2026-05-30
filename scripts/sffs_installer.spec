# -*- mode: python ; coding: utf-8 -*-
"""
sffs_installer.spec — PyInstaller spec for SFFS_USB_Installer.exe

Bundles:
  - sffs_usb_installer.py     (GUI installer script)
  - code1/, code2/, code3/    (SFFS student modules)
  - main-code/                (integration layer + requirements.txt)
  - docs/, scripts/usb-pack/sffs.ico

Output: dist/SFFS_USB_Installer.exe  (~40-70 MB, no Python required on host)

Build:
    cd scripts
    pyinstaller sffs_installer.spec
"""

from pathlib import Path
import os

# Paths
_spec_dir = Path(SPEC).parent          # scripts/
_root     = _spec_dir.parent           # project root

# Collect SFFS source as data (preserved tree under sffs_src/)
def _collect_dir(src_dir: Path, dest_prefix: str) -> list[tuple[str, str]]:
    """Walk src_dir and return list of (abs_file, dest_folder) tuples for datas."""
    items = []
    for path in src_dir.rglob("*"):
        if path.is_file():
            # Skip cache / test artefacts
            parts = path.parts
            if any(p in ("__pycache__", ".git", "test_output", ".mypy_cache") for p in parts):
                continue
            if path.suffix in (".pyc", ".pyo"):
                continue
            rel = path.relative_to(src_dir.parent)
            dest = str(Path(dest_prefix) / rel.parent)
            items.append((str(path), dest))
    return items

_source_dirs = ["code1", "code2", "code3", "main-code", "docs"]
_datas = []

for _d in _source_dirs:
    _src = _root / _d
    if _src.exists():
        _datas += _collect_dir(_src, "sffs_src")

# Include icon
_ico = _spec_dir / "usb-pack" / "sffs.ico"
if not _ico.exists():
    _ico = _spec_dir / "sffs.ico"
if _ico.exists():
    _datas.append((str(_ico), "sffs_src/scripts/usb-pack"))

# Include pre-built launchers if present
for _exe_name in ("SFFS_launcher.exe", "SFFS_worker.exe"):
    _exe_path = _spec_dir / "usb-pack" / "dist" / _exe_name
    if _exe_path.exists():
        _datas.append((str(_exe_path), "sffs_src/scripts/usb-pack/dist"))

a = Analysis(
    [str(_spec_dir / "sffs_usb_installer.py")],
    pathex=[str(_spec_dir)],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        "tkinter",
        "tkinter.ttk",
        "tkinter.font",
        "tkinter.messagebox",
        "queue",
        "threading",
        "ctypes",
        "ctypes.windll",
        "urllib.request",
        "zipfile",
        "shutil",
        "subprocess",
        "pathlib",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt6", "pytest", "numpy", "pandas"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SFFS_USB_Installer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(_ico) if _ico.exists() else None,
    uac_admin=True,         # Auto-elevate UAC
    onefile=True,
    version_file=None,
)
