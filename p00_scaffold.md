# SFFS — Phase 0: Project Scaffold

You are building the SFFS (Smart File Fortify System) — a portable, USB-executable file encryption application for a university graduation project. This is Phase 0: create the complete folder skeleton and foundational files.

## Your Task

Create the following complete directory and file structure. Every file listed below must be created with its full content — not placeholders.

---

## Directory Structure to Create

```
SFFS/
├── code1/__init__.py
├── code2/__init__.py
├── code3/__init__.py
├── main-code/__init__.py
├── main-code/requirements.txt
├── docs/.gitkeep
├── tests/__init__.py
├── tests/test_student1.py       ← stub test file
├── tests/test_student2.py       ← stub test file
├── tests/test_student3.py       ← stub test file
└── main-code/setup.py
```

---

## File Contents

### `code1/__init__.py`
```python
"""
SFFS - Student 1: Crypto-Security Module Package
Functions: generateKeyPairs, encryptFile, decryptFile,
           generateHash, verifyHash, secureKeyStorage
"""
```

### `code2/__init__.py`
```python
"""
SFFS - Student 2: System-Security Module Package
Functions: createIsolatedSandbox, secureMemoryWipe, authenticateUser,
           monitorProcess, writeAuditLog, emergencyLock
"""
```

### `code3/__init__.py`
```python
"""
SFFS - Student 3: System Architect Module Package
Functions: initDriveDetection, uiDashboard, fileManagerExplorer,
           cloudSync, configLoader, threadController
"""
```

### `main-code/__init__.py`
```python
"""
SFFS - Main Integrated System Package
Entry point: main.py
"""
```

### `main-code/requirements.txt`

Include ALL of these dependencies with pinned minimum versions:

```
# Cryptography — Student 1
pycryptodome>=3.19.0
cryptography>=41.0.0

# Password Hashing — Student 2
argon2-cffi>=23.1.0

# Process Monitoring — Student 2
psutil>=5.9.0

# GUI — Student 3
PyQt6>=6.6.0

# Google Drive Cloud Backup — Student 3
google-api-python-client>=2.108.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1

# Utilities (all stdlib but listed for clarity)
# pathlib, sqlite3, ctypes, hashlib, threading, logging — built into Python 3.10+
```

### `main-code/setup.py`

Full setup.py that allows `pip install -e .` for development:

```python
"""
SFFS setup.py — allows pip install -e . for development mode
"""
from setuptools import setup, find_packages

setup(
    name="sffs",
    version="1.0.0",
    description="Smart File Fortify System — Portable Secure File Encryption",
    author="Ibraheem Snineh, Karim Taha, Mazin Alsarahin",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pycryptodome>=3.19.0",
        "cryptography>=41.0.0",
        "argon2-cffi>=23.1.0",
        "psutil>=5.9.0",
        "PyQt6>=6.6.0",
        "google-api-python-client>=2.108.0",
        "google-auth-oauthlib>=1.1.0",
        "google-auth-httplib2>=0.1.1",
    ],
    entry_points={
        "console_scripts": [
            "sffs=main-code.main:main",
        ],
    },
)
```

### `tests/test_student1.py`

Write a complete pytest test file with these test stubs (empty functions with docstrings for now — they will be filled in Phase 1):

- `test_key_pair_generation()` — verifies RSA keys are generated as valid PEM files
- `test_encrypt_produces_sffs_file()` — verifies .sffs output created
- `test_decrypt_restores_original()` — byte-for-byte comparison
- `test_hash_is_deterministic()` — same file always gives same hash
- `test_hash_detects_tampering()` — one-byte change = different hash
- `test_verify_hash_passes_on_intact_file()` — clean round-trip
- `test_verify_hash_fails_on_tampered_file()` — tamper detection

### `tests/test_student2.py`

Stubs for:
- `test_sandbox_created_and_destroyed()`
- `test_sandbox_isolated_from_host()`
- `test_memory_wipe_zeroes_buffer()`
- `test_auth_accepts_correct_password()`
- `test_auth_rejects_wrong_password()`
- `test_auth_locks_after_max_attempts()`
- `test_audit_log_written_and_encrypted()`
- `test_emergency_lock_wipes_sandbox()`

### `tests/test_student3.py`

Stubs for:
- `test_drive_detection_returns_valid_path()`
- `test_config_save_and_load_roundtrip()`
- `test_thread_controller_runs_task_in_background()`
- `test_thread_controller_reports_progress()`
- `test_cloud_sync_encrypts_before_upload()`

---

## After Creating All Files

1. Print a confirmation list of every file created with its size
2. Run: `python -c "import code1; import code2; import code3; print('All packages importable')"` from the SFFS root
3. Run: `pip install -r main-code/requirements.txt --dry-run` and report what would be installed
4. Confirm: **Checkpoint 0 PASSED** or list what is missing

---

## Rules
- Use Python 3.10+ syntax throughout
- Every `__init__.py` must have a proper module docstring
- The requirements.txt must include a comment above each group of dependencies explaining what they are for
- All paths in setup.py must work on both Windows and Linux
