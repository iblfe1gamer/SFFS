# SFFS — Phase 3: Student 3 — System Architect Module

You are building the SFFS (Smart File Fortify System). This is Phase 3: write all 6 system architect function files for Student 3.

**Assume Phases 0, 1, and 2 are complete.** Work inside `code3/`.

---

## Context

Student 3 builds the skeleton that makes the other two modules usable and portable. Without USB portability (`initDriveDetection`), the crypto is tied to one machine. Without threading (`threadController`), the UI freezes during large file operations. Without the UI (`uiDashboard`), no non-technical user can operate the system.

**Key design principle:** Student 3 code must be importable WITHOUT requiring a display server — some CI/testing environments have no screen. Handle `QApplication` creation gracefully when no display is available.

---

## Files to Create

---

### `code3/f13_init_drive_detection.py`

**Function:** `initDriveDetection() -> dict`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `pathlib`, `os`, `sys`, `platform`
   - `psutil` — `# Why: cross-platform disk/partition enumeration; os.listdir('/') is Linux-only, this works on both`

2. **Module docstring** explaining:
   - Why portability requires relative paths: if you hardcode `D:\SFFS\keys\`, the app breaks when USB gets a different drive letter
   - How the app detects its own location: `Path(sys.argv[0]).resolve().parent`
   - The difference between the USB root and the application directory
   - Why all other modules receive paths from this function rather than defining their own

3. **Function `initDriveDetection() -> dict`:**
   - Use `Path(sys.argv[0]).resolve().parent` to find where the script is running from
   - Walk up the directory tree to find the USB root (the mountpoint/drive root)
   - On **Windows:** Detect drive letter (e.g., `D:\`) using `pathlib.Path.anchor`
   - On **Linux:** Use `psutil.disk_partitions()` to find the mount point that contains the script
   - Verify the detected root is removable storage (check `psutil.disk_partitions()` `opts` field for `'removable'`) — if not removable (e.g., running from C:\), warn but don't fail (useful for development)
   - Build the standard SFFS directory map:
     ```python
     {
       "usb_root": Path,          # e.g., D:\ or /media/user/USB
       "app_dir": Path,           # where main.py lives
       "data_dir": Path,          # usb_root/sffs_data/
       "keys_dir": Path,          # usb_root/sffs_data/keys/
       "sandbox_dir": Path,       # usb_root/sffs_data/sandbox/
       "logs_dir": Path,          # usb_root/sffs_data/logs/
       "config_dir": Path,        # usb_root/sffs_data/config/
       "backups_dir": Path,       # usb_root/sffs_data/backups/
       "platform": str,           # "Windows" or "Linux"
       "is_removable": bool,
       "drive_label": str,        # volume label or mount point name
       "free_space_gb": float,
     }
     ```
   - Create all directories if they don't exist (`mkdir(parents=True, exist_ok=True)`)
   - Return the dict

4. **Function `getAvailableSpace(path: Path) -> dict`:**
   - Returns `{"total_gb": float, "used_gb": float, "free_gb": float}`

5. **Function `monitorUSBPresence(usb_root: Path, callback, interval_seconds: float = 0.5)`:**
   - Background thread that calls `callback()` if `usb_root` becomes unavailable
   - Cross-platform using `Path.exists()`

6. **`if __name__ == "__main__":` demo:**
   - Detects the drive and prints the full path map
   - Shows free space
   - Prints a warning if not running from removable media

---

### `code3/f14_ui_dashboard.py`

**Function:** `uiDashboard(session_token, config, paths) -> QMainWindow`

Write a complete Python file that creates the main SFFS PyQt6 window.

1. **Imports with WHY comments:**
   - `from PyQt6.QtWidgets import ...` — `# Why PyQt6: most mature, best-documented Python Qt binding; PyQt5 is older, PySide6 is the official LGPL alternative but PyQt6 has better community resources`
   - `from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData`
   - `from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QColor, QPalette`
   - `pathlib`, `sys`

2. **Module docstring** explaining:
   - Why PyQt6 over Tkinter: Tkinter looks dated and lacks drag-and-drop; PyQt6 is professional-grade
   - Why PyQt6 over Electron: Electron bundles a browser engine (~150MB), PyQt6 is much lighter
   - How signals and slots work in Qt (brief explanation for developers new to Qt)
   - The dashboard layout described before coding it

3. **Class `DragDropZone(QWidget)`:**
   - A styled widget that accepts file drag-and-drop
   - Shows "Drag & Drop files here" text when empty
   - Shows dropped filename when a file is dragged in
   - Changes border color on hover (green) and on drop (blue)
   - Emits signal: `file_dropped = pyqtSignal(str)` with the file path

4. **Class `SFSSDashboard(QMainWindow)`:**
   - Complete main window layout:

   **Top bar:**
   - SFFS logo text (dark red), session user, lock button, logout button

   **Left panel (file operations):**
   - `DragDropZone` widget
   - "Encrypt" and "Decrypt" buttons (disabled until file is selected)
   - Progress bar (hidden until operation starts)
   - Status label: "Ready" / "Encrypting..." / "Decrypted successfully"

   **Right panel (info/alerts):**
   - Security status indicator (green = all clear, red = alert)
   - Last 5 log entries displayed (auto-refreshes every 5 seconds)
   - Cloud sync button + status

   **Bottom bar:**
   - Current session duration, USB free space, version number

   **Methods:**
   - `updateProgress(percent: int)` — updates progress bar
   - `showSecurityAlert(message: str, severity: str)` — shows colored alert banner
   - `setEncryptMode(file_path: str)` — enables encrypt button for selected file
   - `refreshLogs(log_entries: list)` — updates log display panel

5. **Class `LoginWindow(QDialog)`:**
   - Clean login form: username field, password field (masked), Login button
   - Shows error message on auth failure
   - Calls `authenticateUser()` from code2 on submit
   - On success: closes itself and opens `SFSSDashboard`

6. **Function `uiDashboard(session_token: str, config: dict, paths: dict) -> None`:**
   - Creates `QApplication` (check if one already exists first)
   - Creates and shows `SFSSDashboard`
   - Calls `app.exec()`

7. **`if __name__ == "__main__":` demo:**
   - Handle `no display` gracefully: wrap in try/except for headless environments
   - Launch with a dummy session_token and mock config
   - Show the dashboard with mock data

---

### `code3/f15_file_manager_explorer.py`

**Function:** `fileManagerExplorer(root_path, allowed_extensions=None) -> QWidget`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - PyQt6 widgets for the tree view
   - `pathlib`, `os`, `stat`

2. **Module docstring** explaining:
   - Why a custom file browser is used instead of `QFileDialog` (the OS file picker):
     - `QFileDialog` generates OS thumbnail cache files that can expose file names on the host
     - The OS file picker logs recently opened files in registry (Windows) / `~/.recently-used` (Linux)
     - A custom browser scoped to the USB prevents all of this
   - What file operations are blocked: no copy to host OS clipboard, no "Open With" to host apps

3. **Class `SFSSFileModel(QFileSystemModel subclass or custom model)`:**
   - Only shows files within the allowed `root_path`
   - Filters by `allowed_extensions` if provided (e.g., `['.sffs']` for decryption view, `['*']` for encryption view)
   - Shows columns: Name, Size, Modified, Type (`.sffs` / plain)
   - Custom icon for `.sffs` files (lock icon using Qt built-in `QStyle.StandardPixmap.SP_FileLinkIcon`)

4. **Class `FileManagerExplorer(QWidget)`:**
   - Left panel: directory tree (scoped to root_path)
   - Right panel: file list for selected directory
   - Bottom bar: selected file path, file size
   - Double-click on `.sffs` file: emit `sffs_file_selected = pyqtSignal(str)`
   - Double-click on plain file: emit `plain_file_selected = pyqtSignal(str)`
   - Right-click context menu: "Encrypt", "Decrypt", "Delete" (no "Open" — never open on host OS)

5. **`if __name__ == "__main__":` demo:**
   - Open the file manager scoped to the current directory
   - Show it works for file selection

---

### `code3/f16_cloud_sync.py`

**Function:** `cloudSync(action, file_path=None, config=None) -> dict`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `from googleapiclient.discovery import build` — `# Why Google Drive API: most widely available, has a free tier, good Python SDK`
   - `from google_auth_oauthlib.flow import InstalledAppFlow` — `# Why OAuth 2.0: never stores Google credentials — user grants permission via browser`
   - `from google.oauth2.credentials import Credentials`
   - `pathlib`, `json`, `base64`

2. **Module docstring** explaining:
   - Why OAuth 2.0 instead of storing a Google password (OAuth scopes limit what the app can access)
   - The scope used: `https://www.googleapis.com/auth/drive.file` — only files created by SFFS, not full Drive access
   - Why files are encrypted BEFORE leaving the device — Google cannot read the content
   - How to set up a Google Cloud project and get client credentials (brief steps)
   - What happens when offline: all cloud functions return gracefully with `"status": "offline"`

3. **Function `loadCredentials(config_dir: Path) -> Credentials or None`:**
   - Try to load saved OAuth token from `config_dir/google_token.json` (encrypted)
   - Return None if not found or expired

4. **Function `authenticateGoogleDrive(config_dir: Path, client_secrets_path: Path) -> Credentials`:**
   - Run OAuth flow (opens browser for user login)
   - Save token encrypted to `config_dir/google_token.json`
   - Return credentials

5. **Function `cloudSync(action: str, local_path: Path = None, file_id: str = None, config_dir: Path = None) -> dict`:**
   - `action` options: `"upload"`, `"download"`, `"list"`, `"delete"`
   - All files uploaded are named `sffs_{original_name}` in a `SFFS_Backup` folder on Drive
   - On `"upload"`: upload `local_path`, return `{"status": "uploaded", "file_id": str, "drive_path": str}`
   - On `"download"`: download `file_id` to `local_path`, return `{"status": "downloaded", "local_path": Path}`
   - On `"list"`: return list of `{"file_id", "name", "size", "modified"}` dicts
   - If not authenticated: return `{"status": "not_authenticated", "message": "Run authenticateGoogleDrive() first"}`
   - If offline: catch connection errors, return `{"status": "offline", "message": "No internet connection"}`

6. **`if __name__ == "__main__":` demo:**
   - Check for `client_secret.json` in the current directory
   - If present: run full upload/download cycle with a test file
   - If not present: print setup instructions and mock the API calls

---

### `code3/f17_config_loader.py`

**Function:** `configLoader(action, config_dir, updates=None) -> dict`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `json`, `pathlib`, `datetime`
   - `from Crypto.Cipher import AES` — to encrypt the config file at rest
   - `from Crypto.Random import get_random_bytes`

2. **Module docstring** explaining:
   - Why configuration is stored encrypted (OAuth tokens, user preferences might reveal sensitive info)
   - Why JSON is used over SQLite for config (human-readable when decrypted for debugging, simpler structure)
   - The config schema (all fields and their types and defaults)
   - Why config is only accessible after authentication

3. **Default config schema:**
   ```python
   DEFAULT_CONFIG = {
       "version": "1.0",
       "theme": "dark",                    # "dark" | "light"
       "auto_lock_timeout_seconds": 300,   # 5 minutes default
       "max_login_attempts": 5,
       "cloud_sync_enabled": False,
       "cloud_sync_provider": "google_drive",
       "google_oauth_token_path": None,    # set on first cloud auth
       "default_encrypt_dir": None,        # set to USB data dir on init
       "default_decrypt_dir": None,
       "log_max_entries": 10000,
       "hash_algorithm": "sha256",         # "sha256" | "sha512" | "blake2b"
       "key_size_bits": 2048,              # RSA key size
       "pbkdf2_iterations": 310000,
       "ui_show_advanced": False,
       "last_updated": None,
   }
   ```

4. **Function `configLoader(action: str, config_dir: Path, updates: dict = None, encryption_key: bytes = None) -> dict`:**
   - `action = "load"`: decrypt and return config dict (merge with DEFAULT_CONFIG for any missing keys)
   - `action = "save"`: merge `updates` into current config, encrypt and write to `config_dir/sffs_config.enc`
   - `action = "reset"`: overwrite with DEFAULT_CONFIG
   - `action = "get"`: return single value — `updates` = `{"key": "auto_lock_timeout_seconds"}`
   - If `encryption_key` is None: store/load as plain JSON (development mode — warn loudly)
   - Encrypted format: same as keystore JSON (IV + ciphertext + auth_tag in JSON wrapper)

5. **Function `validateConfig(config: dict) -> dict`:**
   - Validate all values are correct types and within acceptable ranges
   - Return `{"valid": bool, "errors": list}`

6. **`if __name__ == "__main__":` demo:**
   - Creates a config in `./code3/test_output/`
   - Saves, loads, modifies a setting, reloads
   - Confirms round-trip integrity

---

### `code3/f18_thread_controller.py`

**Function:** `threadController(task, args=(), progress_callback=None, done_callback=None) -> WorkerThread`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `from PyQt6.QtCore import QThread, pyqtSignal, QObject` — `# Why QThread over threading.Thread: Qt requires UI updates to come from the main thread via signals; QThread integrates with Qt's event loop properly`
   - `threading`, `time`, `traceback`

2. **Module docstring** explaining:
   - Why multi-threading is critical for UX: Python's GIL still allows I/O-bound operations to run concurrently
   - Why PyQt UI updates MUST happen on the main thread (Qt rule — updating widgets from a worker thread crashes)
   - How Qt signals solve this: signals are thread-safe and marshal calls to the main thread automatically
   - Why AES encryption IS I/O-bound for large files (reading disk is slower than AES computation)

3. **Class `WorkerSignals(QObject)`:**
   - `progress = pyqtSignal(int)` — 0–100 percent
   - `result = pyqtSignal(object)` — task return value
   - `error = pyqtSignal(str)` — exception message + traceback
   - `finished = pyqtSignal()` — always emitted when done (success or error)
   - `status_message = pyqtSignal(str)` — human-readable status updates

4. **Class `WorkerThread(QThread)`:**
   - `__init__(self, task: callable, args: tuple, kwargs: dict)`
   - `run(self)`: call `task(*args, **kwargs)`, emit `result` or `error`, always emit `finished`
   - `cancel(self)`: set `self._cancelled = True` — task must check `worker.is_cancelled()` periodically
   - `is_cancelled(self) -> bool`

5. **Function `threadController(task: callable, args: tuple = (), kwargs: dict = None, progress_callback = None, done_callback = None, error_callback = None) -> WorkerThread`:**
   - Create and configure a `WorkerThread`
   - Connect signals to callbacks
   - Call `worker.start()`
   - Return the worker (caller can call `worker.cancel()` if needed)

6. **Decorator `@run_in_thread`:**
   - A decorator that wraps any function to run it in a `WorkerThread` automatically
   - Usage: `@run_in_thread` on `encryptFile` makes it automatically non-blocking

7. **`if __name__ == "__main__":` demo:**
   - Handle no-display gracefully
   - Simulate a 5-second "encryption" task with fake progress updates
   - Show progress bar updating in real time
   - Show result when done

---

### `code3/run_student3.py`

Write an interactive demo runner with menu:

```
SFFS — Student 3: System Architect Demo
========================================
[1] Detect USB drive and show path map
[2] Load / save configuration
[3] Launch UI dashboard (requires display)
[4] Open file manager explorer (requires display)
[5] Test thread controller (background task with progress)
[6] Test cloud sync (requires Google credentials)
[7] Full integration test (headless-safe)
[0] Exit
```

Option [7] headless-safe test:
- Run `initDriveDetection()`
- Run `configLoader()` save/load cycle
- Run `threadController()` with a dummy 3-second task showing progress
- Skip UI and cloud if no display / no credentials
- Print PASS/FAIL report

---

### `code3/README.md`

Complete README covering:
- What this module does
- Prerequisites: `pip install PyQt6 psutil google-api-python-client google-auth-oauthlib`
- How to set up Google Drive API (step-by-step: create project, enable API, download client_secret.json)
- Each function description with signature
- How to run without a display (headless mode — options 1, 2, 5, 7)
- How the UI connects to Student 1 and Student 2 modules
- PyQt6 version requirements (6.6.0+ required for full drag-and-drop support on Linux)

---

## Rules for All Files

- All imports include WHY comments
- All functions have complete docstrings with `Args:`, `Returns:`, `Raises:`, `Notes:`
- Platform differences handled with `platform.system()` checks
- `QApplication` creation wrapped in try/except for headless environments
- Use `pathlib.Path` everywhere
- Every file independently runnable via `if __name__ == "__main__":`

## After All Files Created

Run:
```bash
python code3/f13_init_drive_detection.py
python code3/f17_config_loader.py          # headless-safe
python code3/f18_thread_controller.py      # headless-safe
python code3/run_student3.py               # select option 7
```

Confirm **Checkpoint 3 PASSED**.
