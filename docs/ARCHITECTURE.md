# SFFS Architecture

## 1. System overview

**SFFS** (Smart File Fortify System) encrypts files at rest on a **USB stick** using AES-256-GCM, wraps session keys with RSA-2048, and keeps decrypted material in a **session sandbox** on the USB. It adds authentication (Argon2id), audit logging, optional process monitoring, and optional cloud backup of key material.

Generic full-disk tools (BitLocker, VeraCrypt) either tie to one OS, need admin rights, or encrypt the whole volume. SFFS targets **selective file encryption** with a **portable** layout so the same tree runs on Windows and Linux.

## 2. Module map

```
+-------------------------------------------------------------------+
|                      SFFS Application                              |
|  +-------------+    +-------------+    +-------------+             |
|  |  Student 1  |    |  Student 2  |    |  Student 3   |             |
|  |   code1/    |    |   code2/    |    |   code3/     |             |
|  | Crypto      |    | Runtime sec |    | USB / UI     |             |
|  +------+------+    +------+------+    +------+-------+             |
|         \                 |                  /                        |
|          \                |                 /                         |
|           +------- main-code/sffs_core.py --------+                  |
|                     main-code/main.py                              |
+-------------------------------------------------------------------+
```

## 3. Initialization sequence

1. `initDriveDetection()` — resolve `usb_root`, `app_dir`, create `sffs_data/*` subdirs.  
2. `configLoader("load", config_dir)` — merge defaults, load `sffs_config.enc` or JSON (dev).  
3. `initAuthDatabase(auth.db)` — SQLite users/sessions.  
4. `AuditLogger(logs_dir / "audit.db")` — append-only audit trail.  
5. `ProcessMonitor(..., on_threat_detected)` — optional debugger/heuristic checks.  
6. **After login:** `createIsolatedSandbox(sandbox_dir, session_id)`.  
7. `setupUSBRemovalDetection(usb_root, callback)` — poll for unplug → emergency lock.

## 4. Encrypt flow (GUI / core)

User selects file → **SFFSCore.encryptFileOperation**  
→ ensure RSA keypair + `secureKeyStorage` (keystore under `keys_dir/`)  
→ random 32-byte AES key  
→ `encryptFile` → `.sffs`  
→ `wrapAESKey` → `.aeswrap` next to `.sffs`  
→ `generateHash` / audit log.

## 5. Decrypt flow

User selects `.sffs` → **decryptFileOperation**  
→ controller builds signed IPC envelope (nonce + session binding + HMAC)  
→ spawns `main-code/isolated_worker.py` with strict worker policy  
→ worker unwraps AES key and decrypts into sandbox `decrypted_dir` only  
→ worker verifies `hash_pre == hash_post` and returns structured result  
→ on mismatch or policy/signature failure: delete output, raise `SecurityError`.

### 5.1 Worker boundary and policy

- `isolated_worker.py` is a dedicated decrypt worker process.
- `worker_policy.json` constrains allowed actions and output root.
- Controller and worker use a signed envelope (HMAC-SHA256) with short TTL.
- Emergency triggers terminate active worker processes before global lock.

## 6. Emergency lock

USB missing / debugger / manual lock → `emergencyLock`  
→ wipe memory targets (if provided) → `destroySandbox` → `terminateSession` → CRITICAL audit → `sys.exit`.

## 7. Data flow (summary)

| Data | Form |
|------|------|
| Plaintext file | bytes on disk |
| `.sffs` | magic + header + AES-GCM ciphertext + tag |
| `.aeswrap` | RSA-OAEP–encrypted AES key |
| Keystore JSON | PBKDF2 + AES-GCM–wrapped RSA private key |
| Session | opaque `session_token` in SQLite |

## 8. `.sffs` file format (binary)

| Offset | Size | Field |
|--------|------|--------|
| 0 | 4 | Magic `SFFS` |
| 4 | 1 | Version `0x01` |
| 5 | 16 | IV |
| 21 | 16 | Auth tag (also appended with ciphertext in crypto layer) |
| 37 | 32 | SHA-256 of plaintext (hex stored in logic; raw bytes in file) |
| 69 | 8 | Original size uint64 LE |
| 77+ | N | Ciphertext (+ tag per `cryptography` AESGCM layout) |

*(Exact tag placement matches `code1/f02_encrypt_file.py` / `f03_decrypt_file.py`.)*

## 9. Cross-platform strategy

- Paths: `pathlib.Path` only.  
- Permissions: sandbox uses `chmod` on Linux, `icacls` attempt on Windows.  
- USB root: `psutil` + anchor / mountpoint heuristics (`f13`).  
- GUI: PyQt6; headless/CI: `QCoreApplication` or CLI (`--headless`).
