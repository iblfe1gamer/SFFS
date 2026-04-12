# SFFS — Phase 4: Main Integration

You are building the SFFS (Smart File Fortify System). This is Phase 4: wire all three student modules together into a single runnable application inside `main-code/`.

**Assume Phases 0–3 are complete.** All code1/, code2/, code3/ modules are implemented.

---

## Files to Create

---

### `main-code/sffs_core.py`

Write the central orchestration class that wires all 18 functions together.

```python
"""
sffs_core.py — SFFS Application Core

This module is the "conductor" of the SFFS system. It does not implement
any cryptography, security, or UI itself — instead it:
1. Initializes all modules in the correct order
2. Manages shared state (session, paths, config)
3. Provides high-level operations that the UI can call
4. Ensures the correct cross-module call sequence for each user action

INITIALIZATION ORDER (must be followed):
  1. initDriveDetection()       → establishes all paths
  2. configLoader("load")       → loads user settings
  3. initAuthDatabase()         → prepares auth DB
  4. AuditLogger()              → starts logging
  5. ProcessMonitor()           → starts background security monitor
  6. createIsolatedSandbox()    → (after authentication only)
  7. setupUSBRemovalDetection() → starts USB watchdog

SHUTDOWN ORDER:
  1. emergencyLock() or graceful shutdown
  2. destroySandbox()
  3. terminateSession()
  4. ProcessMonitor.stop()
"""
```

**Class `SFFSCore`:**

```python
class SFFSCore:
    def __init__(self):
        self.paths = None           # from initDriveDetection()
        self.config = None          # from configLoader()
        self.session_token = None   # from authenticateUser()
        self.sandbox = None         # from createIsolatedSandbox()
        self.logger = None          # AuditLogger instance
        self.process_monitor = None # ProcessMonitor instance
        self.current_user = None
        self._emergency_active = False
```

**Methods to implement:**

1. **`initialize() -> dict`**
   - Calls `initDriveDetection()` → stores in `self.paths`
   - Calls `configLoader("load", self.paths["config_dir"])` → stores in `self.config`
   - Calls `initAuthDatabase(self.paths["data_dir"] / "auth.db")`
   - Creates `AuditLogger(self.paths["logs_dir"] / "audit.db")`
   - Starts `ProcessMonitor` with `self._on_threat_detected` as callback
   - Calls `setupUSBRemovalDetection(self.paths["usb_root"], self._on_usb_removed)`
   - Returns `{"status": "ready", "paths": self.paths, "platform": ...}`

2. **`login(username: str, password: bytearray) -> dict`**
   - Calls `authenticateUser(username, password, auth_db_path)`
   - On success: stores `self.session_token`, calls `createIsolatedSandbox()`
   - Logs: `writeAuditLog("User login", "INFO", user_id=...)`
   - Returns auth result dict

3. **`logout()`**
   - Calls `terminateSession(self.session_token)`
   - Calls `destroySandbox(self.sandbox["sandbox_path"])`
   - Logs logout
   - Clears `self.session_token`

4. **`encryptFileOperation(input_path: Path) -> dict`**
   - Validates active session
   - Calls `generateKeyPairs()` if no key exists for this session
   - Calls `secureKeyStorage(private_key_bytes, master_password, self.paths["keys_dir"])`
   - Generates a random AES key
   - Calls `encryptFile(input_path, aes_key, output_path=...)`
   - Calls `wrapAESKey(aes_key, public_key_path)` → stores alongside .sffs
   - Calls `generateHash()` → stored in return dict
   - Wipes AES key from memory
   - Logs the operation
   - Returns `{"sffs_path": Path, "hash_pre": str, "status": "encrypted"}`

5. **`decryptFileOperation(sffs_path: Path, master_password: bytearray) -> dict`**
   - Validates active session
   - Calls `unwrapAESKey()` to get the AES key
   - Calls `decryptFile(sffs_path, aes_key, output_dir=self.sandbox["decrypted_dir"])`
   - Calls `verifyHash(hash_pre, hash_post)` → if CRITICAL_TAMPER_DETECTED: wipe output, raise SecurityError
   - Wipes AES key from memory
   - Logs the operation
   - Returns `{"output_path": Path, "integrity": "verified", "status": "decrypted"}`

6. **`backupKeys() -> dict`**
   - Validates active session and cloud_sync_enabled in config
   - Calls `cloudSync("upload", local_path=self.paths["keys_dir"])`
   - Logs backup event
   - Returns result dict

7. **`_on_threat_detected(threat_type, details)`**
   - Called by ProcessMonitor on debugger/threat detection
   - Calls `emergencyLock("DEBUGGER_DETECTED", ...)`

8. **`_on_usb_removed()`**
   - Calls `emergencyLock("USB_REMOVED", ...)`

---

### `main-code/main.py`

The application entry point. Write a complete file:

```python
"""
main.py — SFFS Entry Point

Run this file to start the SFFS application:
    python main.py                    # Full GUI mode
    python main.py --headless         # CLI mode (for testing)
    python main.py --student 1        # Run only Student 1 demo
    python main.py --student 2        # Run only Student 2 demo
    python main.py --student 3        # Run only Student 3 demo
    python main.py --test             # Run all tests
"""
```

1. **`parse_args()`** — handle command line arguments with `argparse`

2. **`run_full_app()`**:
   - Create `SFFSCore` and call `initialize()`
   - Create `QApplication`
   - Show `LoginWindow`
   - On successful login: show `SFSSDashboard`
   - Connect dashboard signals to `SFFSCore` methods
   - Call `app.exec()`

3. **`run_headless_demo()`**:
   - CLI-mode: print menus, accept keyboard input
   - Full pipeline: initialize → register (first run) → login → encrypt a test file → decrypt → verify → logout
   - No GUI required

4. **`run_student_demo(student_num: int)`**:
   - Routes to the appropriate `run_studentN.py` runner

5. **`run_tests()`**:
   - Run `pytest tests/` and display results

6. **`main()`**:
   - Entry point function — reads args and routes to appropriate function

7. **Cross-platform shebang and encoding header:**
   ```python
   #!/usr/bin/env python3
   # -*- coding: utf-8 -*-
   ```

---

### `main-code/README.md`

Write a comprehensive README covering:

**Project Overview section:**
- What SFFS is and the problem it solves
- The three-student team structure
- Key security features

**Quick Start section:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run full application
python main.py

# Run headless demo
python main.py --headless

# Run individual student demos
python main.py --student 1
python main.py --student 2
python main.py --student 3
```

**Architecture section:**
- Module dependency diagram (ASCII art)
- The initialization sequence
- The encrypt/decrypt call chains

**Security Model section (brief — full version in docs/):**
- AES-256-GCM for file encryption
- RSA-2048 + PBKDF2 for key protection
- Argon2id for password hashing
- SHA-256 for integrity
- Isolated sandbox for runtime protection

---

## After All Files Created

Run:
```bash
python main-code/main.py --headless
```

Confirm **Checkpoint 4 PASSED** — headless pipeline completes without errors.
