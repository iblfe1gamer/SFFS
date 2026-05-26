# SFFS API Reference (F-01 … F-18)

Conventions: paths are `pathlib.Path`. Sensitive passwords use `bytearray` where noted in module docstrings.

---

## F-01 — `generateKeyPairs(output_dir, key_size=2048)` → `dict`

**Module:** `code1/f01_generate_key_pairs.py`  
**Returns:** `public_key_path`, `private_key_bytes`, `key_id`, `generated_at`.  
**Raises:** `ValueError` if `key_size < 2048`.  
**Called by:** `SFFSCore._ensure_rsa_keys`, demos.

---

## F-02 — `encryptFile(input_path, aes_key, output_path=None)` → `dict`

**Module:** `code1/f02_encrypt_file.py`  
**Returns:** `sffs_path`, `hash_pre`, `iv`, `original_size`, `status`.  
**Notes:** Writes `.sffs` binary format.

---

## F-03 — `decryptFile(sffs_path, aes_key, output_dir=None)` → `dict`

**Module:** `code1/f03_decrypt_file.py`  
**Returns:** `output_path`, `hash_pre`, `hash_post`, `original_size`, `status`.  
**Raises:** `SecurityError` on GCM failure / tampering.

---

## F-04 — `generateHash(target: Path | bytes, algorithm="sha256")` → `str`

**Module:** `code1/f04_generate_hash.py`  
**Returns:** Hex digest string.

---

## F-05 — `verifyHash(hash_pre, hash_post)` → `dict`

**Module:** `code1/f05_verify_hash.py`  
**Returns:** `match`, `alert_level`, `message`, truncated hashes.

---

## F-06 — Keystore helpers (`code1/f06_secure_key_storage.py`)

| Function | Purpose |
|----------|---------|
| `secureKeyStorage(private_key_bytes, master_password, output_dir, key_id=None)` | PBKDF2 + AES-GCM wrap; writes `keystore_*.json`. |
| `retrieveKey(keystore_path, master_password)` | Decrypt private key bytes. |
| `wrapAESKey(aes_key, public_key_path)` | RSA-OAEP encrypt AES key. |
| `unwrapAESKey(blob, keystore_path, master_password)` | Decrypt AES key via stored RSA private key. |

---

## F-07 — `createIsolatedSandbox(base_path, session_id=None)` / `destroySandbox`

**Module:** `code2/f07_create_isolated_sandbox.py`  
**Returns:** paths for sandbox, `decrypted_dir`, etc.

---

## F-08 — `secureMemoryWipe(target: bytearray, passes=3)` → `dict`

**Module:** `code2/f08_secure_memory_wipe.py`

---

## F-09 — Auth (`code2/f09_authenticate_user.py`)

| Function | Purpose |
|----------|---------|
| `initAuthDatabase(db_path)` | Create SQLite schema. |
| `registerUser(username, password, db_path)` | Argon2id hash. |
| `authenticateUser(username, password, db_path)` | Session + lockout policy. |
| `terminateSession(token, db_path)` | Invalidate session. |

---

## F-10 — `isDebuggerPresent()` / `checkSuspiciousProcesses()` / `ProcessMonitor`

**Module:** `code2/f10_monitor_process.py`  
**ProcessMonitor:** `(check_interval_ms, on_threat_detected_callback)` — run daemon thread.

---

## F-11 — `AuditLogger` / `writeAuditLog`

**Module:** `code2/f11_write_audit_log.py`  
**Logger:** `log(event, level, module, user_id, metadata)`.  
**Module helper:** `writeAuditLog` uses a process-wide singleton (use `AuditLogger` in `SFFSCore` for isolation).

---

## F-12 — `emergencyLock` / `setupUSBRemovalDetection` / `setupIdleTimeout`

**Module:** `code2/f12_emergency_lock.py`

---

## F-13 — Drive detection (`code3/f13_init_drive_detection.py`)

| Function | Signature | Returns |
|----------|-----------|---------|
| `initDriveDetection` | `() → dict` | Path map: `usb_root`, `app_dir`, `data_dir`, `keys_dir`, `sandbox_dir`, `logs_dir`, `config_dir`, `backups_dir`, `platform`, `is_removable`, `drive_label`, `free_space_gb`. Directories are created if absent. |
| `getAvailableSpace` | `(path: Path) → dict` | `free_gb`, `total_gb`, `used_gb` for the volume containing `path`. |
| `monitorUSBPresence` | `(usb_root: Path, callback, interval_seconds=0.5) → Thread` | Background daemon thread; calls `callback()` once when `usb_root` stops existing. |

**Notes:**
- `initDriveDetection` resolves the USB volume root from `sys.argv[0]`. In development (non-removable disk) it falls back to the repository root and emits a `UserWarning`.
- Raises no exceptions on startup; missing-volume edge cases are handled by warnings.

---

## F-14 — UI Dashboard (`code3/f14_ui_dashboard.py`)

| Class / Function | Purpose |
|-----------------|---------|
| `LoginWindow(paths, parent=None)` | Modal `QDialog`; collects username + password, calls `authenticateUser`, exposes `session_token` property. Shows `QMessageBox.critical` when account is locked (rate-limiting feedback). |
| `SFSSDashboard(session_token, config, paths)` | `QMainWindow`; drag-drop encrypt zone, file list, decrypt / lock / cloud-sync / file-manager actions. |
| `uiDashboard(session_token, config, paths)` | Creates or reuses `QApplication`, applies SFFS dark theme, shows `SFSSDashboard`. Blocking call. |
| `apply_sffs_theme(app: QApplication)` | Applies dark QPalette to the application. |

**Login rate-limiting:** `LoginWindow._try_login` distinguishes between wrong password (`QMessageBox.warning`) and account lock (`QMessageBox.critical` showing locked-until timestamp).

---

## F-15 — File Manager (`code3/f15_file_manager_explorer.py`)

| Symbol | Purpose |
|--------|---------|
| `FileManagerExplorer(root_path, allowed_extensions=None)` | `QWidget`; tree-view file browser rooted at `root_path`. Filters to `allowed_extensions` list (e.g. `[".sffs"]`). Emits `fileSelected(Path)` signal on double-click. |
| `fileManagerExplorer(root_path, allowed_extensions=None)` | Factory: creates and returns a `FileManagerExplorer` widget. |

**Raises:** `RuntimeError` if `root_path` does not exist.

---

## F-16 — Cloud Sync (`code3/f16_cloud_sync.py`)

| Function | Signature | Returns |
|----------|-----------|---------|
| `loadCredentials` | `(config_dir: Path) → Credentials \| None` | Cached Google OAuth2 credentials, or `None` if not yet authenticated. |
| `authenticateGoogleDrive` | `(config_dir: Path, client_secrets_path: Path) → Credentials` | Full OAuth2 flow; stores token in `config_dir`. |
| `cloudSync` | `(action, config_dir, local_path=None, filename=None, …) → dict` | `action ∈ {"upload", "download", "list"}`. Returns status dict with keys `status`, `file_id`, `files`, etc. |

**Safety check (added in security audit):** Before uploading a keystore file, `cloudSync` verifies the JSON contains `{"kdf", "encrypted_private_key", "auth_tag", "iv", "salt"}`. Rejects upload if any field is missing (prevents accidentally uploading raw key material).

**Status values:** `"uploaded"`, `"downloaded"`, `"listed"`, `"offline"`, `"not_authenticated"`, `"error"`.

---

## F-17 — Config Loader (`code3/f17_config_loader.py`)

| Function | Signature | Returns |
|----------|-----------|---------|
| `configLoader` | `(action, config_dir, updates=None, encryption_key=None) → dict` | `action ∈ {"load", "save", "reset"}`. Loads/saves `sffs_config.json`; merges defaults. Optionally AES-GCM encrypts the JSON blob when `encryption_key` (32 bytes) is provided. |
| `validateConfig` | `(config: dict) → dict` | Returns `{"valid": bool, "errors": list[str]}`. Checks required keys and value types. |

**Config keys (defaults):** `idle_timeout_seconds=300`, `auto_lock_on_usb_remove=True`, `max_login_attempts=5`, `cloud_sync_enabled=False`, `theme="dark"`.

---

## F-18 — Thread Controller (`code3/f18_thread_controller.py`)

| Symbol | Purpose |
|--------|---------|
| `WorkerSignals` | `QObject` with signals: `finished(object)`, `error(str)`, `progress(int)`. |
| `WorkerThread(fn, *args, **kwargs)` | `QThread` subclass; runs `fn(*args, **kwargs)` off the GUI thread; emits `finished` or `error`. |
| `threadController(fn, on_finished=None, on_error=None, on_progress=None, *args, **kwargs) → WorkerThread` | Creates, connects signals, and starts a `WorkerThread`. Returns the thread so callers can call `.wait()` if needed. |
| `run_in_thread(fn=None, *, kwargs=None)` | Decorator / callable wrapper that runs `fn` in a `WorkerThread` via `threadController`. |

**Usage:**
```python
def heavy_work():
    time.sleep(2)
    return {"done": True}

t = threadController(heavy_work, on_finished=lambda r: print(r))
```

---

## Integration

**`SFFSCore`** (`main-code/sffs_core.py`) — `initialize`, `login`, `logout`, `encryptFileOperation`, `decryptFileOperation`, `backupKeys`.
