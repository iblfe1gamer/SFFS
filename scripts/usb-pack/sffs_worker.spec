# -*- mode: python ; coding: utf-8 -*-
"""
sffs_worker.spec — PyInstaller spec for SFFS_worker.exe

Onefile build of isolated_worker.py with hidden partition discovery.
"""

import os
from pathlib import Path

_spec_dir = Path(SPEC).parent
_root = _spec_dir.parent.parent  # SFFS root

# Collect hidden_volume.py as a data file since it's used at runtime
a = Analysis(
    [_root / "main-code" / "isolated_worker.py", _spec_dir / "hidden_volume.py"],
    pathex=[
        str(_root / "code1"),
        str(_root / "code2"),
        str(_root / "code3"),
        str(_root / "main-code"),
        str(_spec_dir),
    ],
    binaries=[],
    datas=[
        (str(_root / "main-code" / "worker_policy.json"), "."),
    ],
    hiddenimports=[
        "hidden_volume",
        "f03_decrypt_file",
        "f05_verify_hash",
        "f06_secure_key_storage",
        "f02_encrypt_file",
        "f04_generate_hash",
        "f01_generate_key_pairs",
        "f07_create_isolated_sandbox",
        "f08_secure_memory_wipe",
        "f09_authenticate_user",
        "f10_monitor_process",
        "f11_write_audit_log",
        "f12_emergency_lock",
        "f13_init_drive_detection",
        "f14_ui_dashboard",
        "f15_file_manager_explorer",
        "f16_cloud_sync",
        "f17_config_loader",
        "f18_thread_controller",
        "wrap_store",
        "mouse_entropy",
        "sandbox_viewer",
        "os_isolation",
        "secure_app_launcher",
        "Crypto",
        "Crypto.Cipher",
        "Crypto.Cipher.AES",
        "Crypto.Random",
        "cryptography",
        "cryptography.hazmat",
        "cryptography.hazmat.primitives",
        "cryptography.hazmat.primitives.ciphers",
        "cryptography.hazmat.primitives.ciphers.aead",
        "cryptography.hazmat.primitives.kdf",
        "cryptography.hazmat.primitives.kdf.pbkdf2",
        "cryptography.hazmat.primitives.serialization",
        "cryptography.hazmat.backends",
        "cryptography.exceptions",
        "argon2",
        "argon2.low_level",
        "psutil",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "PyQt6",
        "google",
        "googleapiclient",
        "google_auth_oauthlib",
        "google_auth_httplib2",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SFFS_worker",
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
    onefile=True,
)
