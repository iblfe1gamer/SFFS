# -*- mode: python ; coding: utf-8 -*-
"""
sffs_bootstrap.spec — PyInstaller spec for SFFS_launcher.exe

Onefile build with UAC admin auto-elevation and custom icon.
"""

import os
from pathlib import Path

# Resolve paths relative to this spec file
_spec_dir = Path(SPEC).parent
_root = _spec_dir.parent.parent  # SFFS root

a = Analysis(
    [_spec_dir / "launcher_main.py", _spec_dir / "hidden_volume.py"],
    pathex=[str(_spec_dir)],
    binaries=[],
    datas=[],
    hiddenimports=["hidden_volume", "ctypes", "pathlib", "subprocess"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "email", "http", "xml", "pydoc"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SFFS_launcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(_spec_dir / "sffs.ico"),
    uac_admin=True,
    onefile=True,
)
