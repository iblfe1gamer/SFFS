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

## F-13 — `initDriveDetection()` / `getAvailableSpace` / `monitorUSBPresence`

**Module:** `code3/f13_init_drive_detection.py`

---

## F-14 — `uiDashboard` / `SFSSDashboard` / `LoginWindow`

**Module:** `code3/f14_ui_dashboard.py`

---

## F-15 — `fileManagerExplorer(root_path, allowed_extensions=None)`

**Module:** `code3/f15_file_manager_explorer.py`

---

## F-16 — `cloudSync` / `authenticateGoogleDrive` / `loadCredentials`

**Module:** `code3/f16_cloud_sync.py`  
**Returns:** status dict (`uploaded`, `offline`, `not_authenticated`, …).

---

## F-17 — `configLoader(action, config_dir, updates=None, encryption_key=None)` / `validateConfig`

**Module:** `code3/f17_config_loader.py`

---

## F-18 — `threadController` / `WorkerThread` / `run_in_thread`

**Module:** `code3/f18_thread_controller.py`

---

## Integration

**`SFFSCore`** (`main-code/sffs_core.py`) — `initialize`, `login`, `logout`, `encryptFileOperation`, `decryptFileOperation`, `backupKeys`.
