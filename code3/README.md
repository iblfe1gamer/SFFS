# SFFS — Student 3: System Architect Module

Portable path resolution, PyQt6 UI shell, scoped file browser, optional Google Drive backup, encrypted configuration, and Qt worker threads for long-running crypto/file work.

## Prerequisites

```bash
pip install PyQt6 psutil google-api-python-client google-auth-oauthlib pycryptodome
```

Or from repo root:

```bash
pip install -r main-code/requirements.txt
```

PyQt6 **6.6.0+** is recommended for consistent drag-and-drop on Wayland/X11.

## Run the demo menu

```bash
python code3/run_student3.py
```

Headless-friendly options: **1**, **2**, **5**, **7**. Options **3** and **4** need a display server.

## Module map

| Module | Primary API |
|--------|-------------|
| `f13_init_drive_detection.py` | `initDriveDetection()`, `getAvailableSpace()`, `monitorUSBPresence()` |
| `f14_ui_dashboard.py` | `uiDashboard(session_token, config, paths)` |
| `f15_file_manager_explorer.py` | `fileManagerExplorer(root_path, allowed_extensions)` |
| `f16_cloud_sync.py` | `cloudSync(...)`, `authenticateGoogleDrive()`, `loadCredentials()` |
| `f17_config_loader.py` | `configLoader(action, config_dir, ...)`, `validateConfig()` |
| `f18_thread_controller.py` | `threadController()`, `WorkerThread`, `@run_in_thread` |

## Google Drive

1. Create a Google Cloud project, enable the Drive API.
2. Create OAuth **Desktop** credentials and download `client_secret.json`.
3. Call `authenticateGoogleDrive(config_dir, Path("client_secret.json"))` once.
4. Use `cloudSync("upload", local_path=..., config_dir=...)`.

Files should already be encrypted (Student 1) before upload.

## Connecting to Students 1 & 2

- **Paths:** Use `initDriveDetection()` so keys, logs, sandboxes, and `auth.db` live under the same USB tree.
- **Login:** `f14_ui_dashboard.LoginWindow` calls `authenticateUser` from `code2` against `paths["data_dir"] / "auth.db"`.
- **Crypto ops:** The integrated app (`main-code`, Phase 4) should call Student 1 encrypt/decrypt from dashboard actions (not implemented inside this package alone).

## No display / CI

Use `QCoreApplication` plus `WorkerThread` (see `run_student3.py` option 7) or run modules `f13`, `f17` standalone.
