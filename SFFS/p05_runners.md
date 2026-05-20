# SFFS — Phase 5: Runners, Tests & Launchers

You are building SFFS (Smart File Fortify System). This is Phase 5: finalize all runner scripts, test files, and OS launcher scripts.

**Assume Phases 0–4 are complete.**

---

## Task 1: Fill in Test Stubs

Fill in the stub test functions created in Phase 0 with real test logic using `pytest`.

### `tests/test_student1.py`

Complete all test functions. Use `tmp_path` pytest fixture for temporary directories. Each test should:
- Set up a realistic scenario
- Call the actual function from code1
- Assert the expected result
- Clean up after itself

Key tests:
- `test_decrypt_restores_original`: Encrypt `b"Hello World"`, decrypt, assert bytes identical
- `test_hash_detects_tampering`: Hash `b"original"`, hash `b"0riginal"` (zero instead of O), assert they differ
- `test_verify_hash_fails_on_tampered_file`: Encrypt, flip byte 100 of the .sffs file, attempt decrypt, assert `SecurityError` raised
- `test_key_retrieval_fails_wrong_password`: Store key with `"correct_pass"`, retrieve with `"wrong_pass"`, assert raises

### `tests/test_student2.py`

Complete all test functions:
- `test_sandbox_created_and_destroyed`: Create sandbox, assert dir exists, destroy, assert dir gone
- `test_memory_wipe_zeroes_buffer`: Create `bytearray(b"secret")`, wipe, assert all bytes are 0
- `test_auth_rejects_wrong_password`: Register user, authenticate with wrong password, assert `authenticated == False`
- `test_audit_log_written_and_encrypted`: Write log entry, reload logger, assert entry retrievable
- `test_emergency_lock_wipes_sandbox`: Create sandbox, call emergencyLock(MANUAL), but intercept sys.exit — assert sandbox destroyed

### `tests/test_student3.py`

Complete all test functions:
- `test_drive_detection_returns_valid_path`: Call `initDriveDetection()`, assert all required keys present in result
- `test_config_save_and_load_roundtrip`: Save config with modified value, reload, assert value preserved
- `test_thread_controller_runs_task_in_background`: Run 0.5s sleep task in thread, assert it doesn't block test for > 0.1s on the main thread

---

## Task 2: Create OS Launcher Scripts

### `sffs.bat` (Windows launcher — place in SFFS root)

```batch
@echo off
:: SFFS Windows Launcher
:: Double-click this file to start SFFS from the USB drive
:: It automatically finds Python (portable or system-installed)

title SFFS — Smart File Fortify System

:: Try portable Python first (bundled on USB)
if exist "%~dp0python\python.exe" (
    set PYTHON="%~dp0python\python.exe"
    echo Using portable Python...
) else (
    set PYTHON=python
    echo Using system Python...
)

:: Check Python version
%PYTHON% -c "import sys; assert sys.version_info >= (3,10), 'Python 3.10+ required'" 2>nul
if errorlevel 1 (
    echo ERROR: Python 3.10 or newer is required.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist "%~dp0.deps_installed" (
    echo Installing dependencies for first run...
    %PYTHON% -m pip install -r "%~dp0main-code\requirements.txt" --quiet
    echo. > "%~dp0.deps_installed"
    echo Dependencies installed.
)

:: Launch SFFS
echo Starting SFFS...
cd /d "%~dp0"
%PYTHON% main-code\main.py %*
pause
```

### `sffs.sh` (Linux launcher — place in SFFS root)

```bash
#!/usr/bin/env bash
# SFFS Linux Launcher
# Run: bash sffs.sh
# Or make executable: chmod +x sffs.sh && ./sffs.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== SFFS — Smart File Fortify System ==="

# Check Python version
PYTHON=$(which python3 2>/dev/null || which python 2>/dev/null)
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found. Install with: sudo apt install python3"
    exit 1
fi

VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED="3.10"

if [ "$(printf '%s\n' "$REQUIRED" "$VERSION" | sort -V | head -n1)" != "$REQUIRED" ]; then
    echo "ERROR: Python $REQUIRED+ required (found $VERSION)"
    exit 1
fi

# Install dependencies on first run
if [ ! -f ".deps_installed" ]; then
    echo "Installing dependencies (first run)..."
    $PYTHON -m pip install -r main-code/requirements.txt --quiet --user
    touch .deps_installed
    echo "Dependencies installed."
fi

# Check for display (for GUI mode)
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "No display detected — launching in headless mode"
    $PYTHON main-code/main.py --headless "$@"
else
    $PYTHON main-code/main.py "$@"
fi
```

### `sffs_install_deps.py` (Dependency installer — cross-platform)

Write a Python script that:
- Checks Python version
- Checks which packages are missing
- Installs only what's missing
- Handles pip not being available (shows instructions)
- Works on both Windows and Linux
- Prints a clear success/failure summary

---

## Task 3: Update `tests/__init__.py`

Add:
```python
"""
SFFS Test Suite
Run all tests: pytest tests/
Run one file:  pytest tests/test_student1.py -v
Run one test:  pytest tests/test_student1.py::test_decrypt_restores_original -v
"""
import sys
from pathlib import Path
# Add SFFS root to path so all modules importable
sys.path.insert(0, str(Path(__file__).parent.parent))
```

---

## After All Files Created

```bash
# Run all tests
pytest tests/ -v

# Run launchers
bash sffs.sh --headless          # Linux
sffs.bat --headless              # Windows (in cmd)
```

Confirm **Checkpoint 5 PASSED** — all tests pass, both launchers work.
