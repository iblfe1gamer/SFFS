# SFFS — Phase 2: Student 2 — System-Security Module

You are building the SFFS (Smart File Fortify System). This is Phase 2: write all 6 system-security function files for Student 2.

**Assume Phases 0 and 1 are complete.** `code1/` is fully implemented. Work inside `code2/`.

---

## Context

Student 2 owns runtime security: the isolated execution environment, memory protection, authentication, process monitoring, audit logging, and the emergency kill-switch. This is the most complex module in the project — the Gantt chart allocates 84 days for the isolated execution environment alone.

**Key design principle:** All Student 2 functions must degrade gracefully — if a security operation fails, the system locks down rather than continuing.

**Integration points:**
- `createIsolatedSandbox()` receives its base path from Student 3's `initDriveDetection()`
- `writeAuditLog()` is called by ALL other modules across all three students
- `emergencyLock()` can be triggered by Student 3's `configLoader()` (auto-lock timer) and by `monitorProcess()`
- `authenticateUser()` gates access to Student 1's `secureKeyStorage()` and Student 3's `uiDashboard()`

---

## Files to Create

---

### `code2/f07_create_isolated_sandbox.py`

**Function:** `createIsolatedSandbox(base_path, session_id=None) -> dict`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `pathlib`, `os`, `stat`, `shutil`, `tempfile`, `uuid`, `platform`
   - `# Why pathlib: cross-platform path handling — avoids Windows/Linux separator issues`
   - `# Why stat: to set restrictive file permissions programmatically`
   - `# Why platform: different permission models on Windows vs Linux`

2. **Module docstring** explaining:
   - What an isolated execution environment is and why it matters
   - The threat model: malware on the host OS, forensic recovery from disk
   - How the sandbox differs from just using a temp directory
   - Why decrypted files must NEVER touch the host OS file system
   - Limitations on each platform (Windows vs Linux)

3. **Function `createIsolatedSandbox(base_path: Path, session_id: str = None) -> dict`:**
   - Generate `session_id = uuid4()` if not provided
   - Create sandbox directory: `base_path/sandbox_{session_id}/`
   - **On Linux:** `os.chmod(sandbox_path, 0o700)` — owner-only access
   - **On Windows:** Use `os.system('icacls ... /inheritance:r /grant ...')` to remove inherited permissions and grant only current user access. Include a comment explaining why `stat` module alone is insufficient on Windows for true ACL control.
   - Create subdirectories: `sandbox/decrypted/`, `sandbox/temp/`, `sandbox/keys_runtime/`
   - Write a `sandbox.lock` file containing `session_id` and timestamp
   - Return dict: `{"sandbox_path": Path, "session_id": str, "decrypted_dir": Path, "temp_dir": Path, "keys_runtime_dir": Path, "created_at": str, "platform": str}`

4. **Function `destroySandbox(sandbox_path: Path) -> bool`:**
   - Calls `secureWipeDirectory()` (defined below)
   - Removes the directory tree
   - Returns True if completely removed

5. **Function `secureWipeDirectory(directory: Path)`:**
   - Walk all files in the directory
   - For each file: overwrite with zeros, then ones, then random bytes (3-pass DOD 5220.22-M)
   - Then delete each file
   - Then remove all subdirectories
   - Include comments explaining why standard `shutil.rmtree` is NOT sufficient for secure deletion

6. **Function `isSandboxIntact(sandbox_path: Path) -> bool`:**
   - Check the `sandbox.lock` file exists and is readable
   - Check permissions are still restrictive (warn if changed)
   - Return False if anything is unexpected

7. **`if __name__ == "__main__":` demo:**
   - Creates a sandbox, prints its structure
   - Creates a test file inside it
   - Destroys it
   - Confirms the directory no longer exists

---

### `code2/f08_secure_memory_wipe.py`

**Function:** `secureMemoryWipe(target, passes=3) -> dict`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `ctypes` — `# Why: only way in Python to directly manipulate raw memory addresses; gc and del are NOT sufficient`
   - `os`, `sys`, `platform`, `secrets`

2. **Module docstring** explaining:
   - Why Python's `del` keyword does NOT erase memory (garbage collector timing)
   - What a cold boot attack is: attacker freezes RAM and reads it after power-off
   - What a memory dump / process memory dump is (attacker tool)
   - The DOD 5220.22-M standard: 3-pass overwrite (0x00, 0xFF, random)
   - Why `bytearray` is used instead of `bytes` for sensitive data (bytearray is mutable)
   - Limitations: Python strings are immutable — once created they cannot be wiped (always use `bytearray` for passwords)

3. **Function `secureMemoryWipe(target: bytearray, passes: int = 3) -> dict`:**
   - Accept a `bytearray` (mutable) object
   - Pass 1: overwrite with `0x00`
   - Pass 2: overwrite with `0xFF`
   - Pass 3: overwrite with `os.urandom(len(target))`
   - Use `ctypes.memmove` or `ctypes.memset` for low-level overwrites where possible
   - Zero the bytearray after all passes
   - Return dict: `{"bytes_wiped": int, "passes_completed": int, "status": "wiped"}`
   - Raise `TypeError` if target is not a `bytearray` (explain in the error message why `bytes` and `str` cannot be wiped)

4. **Function `wipeString(s: str) -> str`:**
   - Attempt best-effort wipe of string via `ctypes`
   - Include a prominent comment: this is best-effort only — Python strings are immutable and interned by the interpreter
   - Return an empty string as replacement

5. **Function `createSecureBuffer(size: int) -> bytearray`:**
   - Returns a zeroed `bytearray` of the given size
   - Intended usage: always create sensitive buffers with this function so they can be wiped later

6. **`if __name__ == "__main__":` demo:**
   - Creates a bytearray containing `b"SecretPassword123"`
   - Prints the memory address and content before wipe
   - Wipes it
   - Prints the memory address and content after wipe (should be all zeros)
   - Demonstrates that the original variable now contains zeros

---

### `code2/f09_authenticate_user.py`

**Function:** `authenticateUser(username, password, db_path) -> dict`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `argon2` from `argon2-cffi` — `# Why Argon2id: winner of the Password Hashing Competition (PHC), memory-hard — resistant to GPU and ASIC brute-force attacks; preferred over PBKDF2 or bcrypt for new systems`
   - `sqlite3` — for credential storage
   - `pathlib`, `datetime`, `secrets`, `hmac`
   - Import `secureMemoryWipe` from `f08_secure_memory_wipe`

2. **Module docstring** explaining:
   - What Argon2id is: a memory-hard KDF that requires large amounts of RAM to compute, making GPU attacks expensive
   - Parameters used: `time_cost=3`, `memory_cost=65536` (64 MB), `parallelism=4`, `hash_len=32`
   - Why these parameters (OWASP 2023 recommendations)
   - Why the plain-text password must be wiped from memory immediately after hashing
   - The lockout policy: exponential backoff (30s, 60s, 120s, 5min...)
   - Why `hmac.compare_digest()` is used for hash comparison (timing attack prevention)

3. **Function `initAuthDatabase(db_path: Path)`:**
   - Creates SQLite database with `users` table:
     - `user_id TEXT PRIMARY KEY`
     - `username TEXT UNIQUE NOT NULL`
     - `password_hash TEXT NOT NULL` (Argon2id hash string)
     - `created_at TEXT`
     - `last_login TEXT`
     - `failed_attempts INTEGER DEFAULT 0`
     - `locked_until TEXT`
   - Also create `sessions` table:
     - `session_token TEXT PRIMARY KEY`
     - `user_id TEXT`
     - `created_at TEXT`
     - `expires_at TEXT`

4. **Function `registerUser(username: str, password: bytearray, db_path: Path) -> dict`:**
   - Validate password policy: min 12 chars, requires uppercase, lowercase, digit, special char
   - Hash with Argon2id
   - Wipe `password` bytearray immediately after hashing
   - Insert into users table
   - Return `{"user_id": str, "status": "registered"}`

5. **Function `authenticateUser(username: str, password: bytearray, db_path: Path) -> dict`:**
   - Check if account is locked (compare `locked_until` to now)
   - Load stored Argon2id hash for username
   - Verify password with Argon2id
   - **IMMEDIATELY** call `secureMemoryWipe(password)` regardless of result
   - On success: reset `failed_attempts` to 0, update `last_login`, generate session token (`secrets.token_urlsafe(32)`), insert into sessions table
   - On failure: increment `failed_attempts`, apply exponential lockout
   - Return dict: `{"authenticated": bool, "session_token": str or None, "user_id": str or None, "locked_until": str or None, "failed_attempts": int, "message": str}`

6. **Function `validateSession(session_token: str, db_path: Path) -> bool`:**
   - Check token exists in sessions table and has not expired

7. **Function `terminateSession(session_token: str, db_path: Path)`:**
   - Delete session from table

8. **`if __name__ == "__main__":` demo:**
   - Creates a test database in `./code2/test_output/`
   - Registers user `testuser` with password `TestPassword123!`
   - Authenticates successfully
   - Attempts wrong password
   - Shows lockout after 5 failures
   - Cleans up test database

---

### `code2/f10_monitor_process.py`

**Function:** `monitorProcess(check_interval_ms=500) -> None` (runs in background thread)

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `psutil` — `# Why: cross-platform process introspection; only way to inspect process relationships and open handles in Python`
   - `threading`, `platform`, `ctypes`, `os`, `sys`, `time`
   - Conditional import: `import ctypes` for Windows debugger detection API

2. **Module docstring** explaining:
   - What debugger attachment means: an attacker runs a tool that pauses SFFS and reads its memory
   - What memory scanners do: scan RAM for encryption key patterns
   - APIs used per platform:
     - Windows: `IsDebuggerPresent()` and `CheckRemoteDebuggerPresent()` via `kernel32.dll`
     - Linux: read `/proc/self/status` and check `TracerPid` field
   - Why this check runs every 500ms (balance between detection speed and CPU usage)
   - Limitations: this is a defense-in-depth measure, not a guarantee

3. **Function `isDebuggerPresent() -> bool`:**
   - **Windows:** `ctypes.windll.kernel32.IsDebuggerPresent()` returns non-zero if debugger attached
   - **Linux:** open `/proc/self/status`, find `TracerPid:` line, non-zero means traced
   - **Cross-platform comment** explaining each platform's mechanism

4. **Function `checkSuspiciousProcesses() -> list`:**
   - Use `psutil.process_iter()` to scan running processes
   - Flag processes whose names match a list of known debugging/analysis tools:
     - Windows: `x64dbg.exe`, `ollydbg.exe`, `windbg.exe`, `ida64.exe`, `processhacker.exe`, `wireshark.exe`
     - Linux: `gdb`, `strace`, `ltrace`, `radare2`, `frida`, `valgrind`
   - Return list of suspicious process names found

5. **Class `ProcessMonitor(threading.Thread)`:**
   - Background daemon thread
   - `__init__(self, check_interval_ms, on_threat_detected_callback)`: stores callback
   - `run(self)`: loop calling `isDebuggerPresent()` and `checkSuspiciousProcesses()` every `check_interval_ms`
   - On threat: call `on_threat_detected_callback(threat_type, details)` and set `self.threat_detected = True`
   - `stop(self)`: sets a threading.Event to terminate the loop cleanly

6. **`if __name__ == "__main__":` demo:**
   - Starts the monitor
   - Prints "Monitoring... (press Ctrl+C to stop)"
   - Shows check results every 2 seconds
   - Stops cleanly on Ctrl+C

---

### `code2/f11_write_audit_log.py`

**Function:** `writeAuditLog(event, level, metadata=None) -> dict`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `sqlite3` — `# Why: built-in, lightweight, no server needed — perfect for USB-portable logging`
   - `from Crypto.Cipher import AES` — to encrypt the log database
   - `pathlib`, `datetime`, `json`, `threading`, `hashlib`

2. **Module docstring** explaining:
   - Why logs must be encrypted (otherwise an attacker reads audit trail)
   - Why logs must be append-only (otherwise an attacker covers tracks)
   - The log rotation strategy: FIFO — delete oldest entries when size limit is reached
   - Why a threading Lock is used (multiple modules call writeAuditLog concurrently)
   - The log levels: DEBUG, INFO, WARN, ERROR, CRITICAL

3. **Class `AuditLogger`:**
   - `__init__(self, db_path: Path, encryption_key: bytes = None)`
   - Uses a threading.Lock for thread-safe writes
   - If `encryption_key` provided, encrypts the SQLite file after each write (WAL mode OFF for simplicity; note the trade-off)
   - Create table `audit_log`:
     - `log_id INTEGER PRIMARY KEY AUTOINCREMENT`
     - `timestamp TEXT NOT NULL`
     - `level TEXT NOT NULL` (DEBUG/INFO/WARN/ERROR/CRITICAL)
     - `event TEXT NOT NULL`
     - `module TEXT`
     - `user_id TEXT`
     - `metadata TEXT` (JSON string)
     - `entry_hash TEXT` (SHA-256 of all other fields — tamper detection)

4. **Method `log(self, event: str, level: str = "INFO", module: str = "SFFS", user_id: str = None, metadata: dict = None) -> dict`:**
   - Acquire threading lock
   - Build the log entry
   - Compute `entry_hash = SHA-256(timestamp + level + event + metadata_json)`
   - Insert into database
   - Check if rotation needed (call `rotateLogs()` if over limit)
   - Release lock
   - Return `{"log_id": int, "timestamp": str, "status": "written"}`

5. **Method `rotateLogs(self, max_entries: int = 10000)`:**
   - Count entries; if over `max_entries`, delete oldest `(count - max_entries)` rows
   - Log the rotation itself as an INFO event

6. **Method `viewLogs(self, level_filter: str = None, limit: int = 100) -> list`:**
   - Return list of log dicts, newest first
   - Optional filter by level

7. **Method `verifyLogIntegrity(self) -> dict`:**
   - Re-compute entry_hash for each row and compare to stored value
   - Return `{"total": int, "valid": int, "tampered": int, "tampered_ids": list}`

8. **Module-level convenience function `writeAuditLog(event, level="INFO", module="SFFS", metadata=None)`:**
   - Global singleton logger instance (initialized on first call)
   - So any module can call `from code2.f11_write_audit_log import writeAuditLog` and use it directly

9. **`if __name__ == "__main__":` demo:**
   - Writes 10 log entries at different levels
   - Shows viewLogs() output
   - Verifies log integrity passes
   - Demonstrates that modifying a log entry causes verifyLogIntegrity() to flag it

---

### `code2/f12_emergency_lock.py`

**Function:** `emergencyLock(trigger, sandbox_path=None, session_token=None) -> None`

Write a complete Python file that:

1. **Imports with WHY comments:**
   - `signal` — `# Why: allows catching OS signals (SIGTERM, SIGHUP) for clean shutdown on USB removal`
   - `threading`, `pathlib`, `sys`, `os`, `time`
   - Import from sibling modules: `secureMemoryWipe`, `destroySandbox`, `writeAuditLog`, `terminateSession`

2. **Module docstring** explaining:
   - The threat model: what happens if the USB is pulled while files are decrypted
   - The sequence of operations that must happen in < 500ms
   - Why the log write happens LAST (so we know the lock completed)
   - Why `sys.exit()` is called at the end (don't trust atexit or garbage collection)
   - The difference between triggers and what each means:
     - `USB_REMOVED`: physical removal — immediate, no user prompt
     - `DEBUGGER_DETECTED`: security threat — immediate, log threat details
     - `TIMEOUT`: idle timeout — graceful, can be resumed with re-authentication
     - `MANUAL`: user pressed lock button — graceful
     - `MAX_FAILURES`: too many wrong passwords — immediate

3. **Function `emergencyLock(trigger: str, sandbox_path: Path = None, session_token: str = None, db_path: Path = None, wipe_memory_targets: list = None) -> None`:**
   - Step 1: Set a global `EMERGENCY_ACTIVE = True` flag (all other operations check this flag)
   - Step 2: Close all open file handles in the application
   - Step 3: If `wipe_memory_targets` provided (list of bytearrays): wipe each with `secureMemoryWipe()`
   - Step 4: If `sandbox_path` provided: call `destroySandbox(sandbox_path)`
   - Step 5: If `session_token` provided: call `terminateSession(session_token, db_path)`
   - Step 6: Write to audit log: `CRITICAL — Emergency lock triggered by {trigger}`
   - Step 7: `sys.exit(0)` — hard termination
   - Each step must be wrapped in try/except — if a step fails, skip it and continue to next
   - Target: complete all steps in < 500ms total

4. **Function `setupUSBRemovalDetection(usb_root: Path, lock_callback)`:**
   - **Windows:** Use `ctypes.windll.user32.RegisterDeviceNotificationW` or poll drive availability every 500ms (polling is simpler and more portable)
   - **Linux:** Use `pathlib.Path.exists()` polling on the USB mount point every 500ms
   - Runs in a background daemon thread
   - Calls `lock_callback("USB_REMOVED")` when USB disappears
   - Include note explaining why kernel-level inotify would be better but is Linux-only

5. **Function `setupIdleTimeout(timeout_seconds: int, lock_callback)`:**
   - Background thread that resets a countdown on activity
   - `resetTimer()`: call this on any user action (key press, mouse click)
   - When countdown reaches 0: calls `lock_callback("TIMEOUT")`

6. **`if __name__ == "__main__":` demo:**
   - Creates a test sandbox
   - Simulates a `MANUAL` trigger
   - Confirms sandbox was destroyed and session terminated
   - Shows the audit log entry

---

### `code2/run_student2.py`

Write an interactive demo runner with menu:

```
SFFS — Student 2: System-Security Demo
=======================================
[1] Create isolated sandbox (and inspect its permissions)
[2] Demonstrate secure memory wipe
[3] Register and authenticate a user
[4] Test lockout policy (fail 5 times)
[5] Start process monitor (10 second scan)
[6] Write and verify audit log
[7] Simulate emergency lock (MANUAL trigger)
[8] Full security pipeline test (all functions)
[0] Exit
```

Option [8] full pipeline:
- Create sandbox
- Register user
- Authenticate
- Write audit log entries for each step
- Start process monitor briefly
- Trigger emergency lock (MANUAL)
- Verify sandbox is destroyed
- Print PASS/FAIL report for each step

---

### `code2/README.md`

Write a complete README covering:
- What this module does and why it matters
- Prerequisites: `pip install argon2-cffi psutil pycryptodome`
- Each function description with its signature
- The threat model: what attacks each function defends against
- Platform notes (Windows vs Linux differences for sandbox, process monitoring, USB detection)
- How this module integrates with Student 1 and Student 3
- Security warning: "Never run SFFS on a VM with shared clipboard/folders — the host can read VM memory"

---

## Rules for All Files

- All imports include WHY comments
- All functions have complete docstrings with `Args:`, `Returns:`, `Raises:`, `Security Notes:`
- Comments explain WHY decisions were made, not just what the code does
- Use `pathlib.Path` everywhere
- Platform differences (Windows/Linux) are always handled with `platform.system()` checks
- Every function that touches sensitive data calls `secureMemoryWipe()` when done

## After All Files Created

Run:
```bash
python code2/f07_create_isolated_sandbox.py
python code2/f08_secure_memory_wipe.py
python code2/f09_authenticate_user.py
python code2/f10_monitor_process.py
python code2/f11_write_audit_log.py
python code2/f12_emergency_lock.py
python code2/run_student2.py  # select option 8
```

Confirm **Checkpoint 2 PASSED** — all 6 files run cleanly, the pipeline test shows all steps PASS.
