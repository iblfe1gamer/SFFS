# Graph Report - .  (2026-05-19)

## Corpus Check
- 686 files · ~287,275 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 619 nodes · 508 edges · 289 communities detected
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 37 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `AuditLogger` - 30 edges
2. `SFFSCore` - 28 edges
3. `WrapStore` - 15 edges
4. `ProcessMonitor` - 14 edges
5. `SFSSDashboard` - 12 edges
6. `DragDropZone` - 10 edges
7. `_DbContext` - 9 edges
8. `resolve_launch()` - 8 edges
9. `main()` - 8 edges
10. `LauncherPolicyError` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Student 2 — system security module tests.` --uses--> `AuditLogger`  [INFERRED]
  SFFS\tests\test_student2.py → SFFS\code2\f11_write_audit_log.py
- `sffs_core.py — SFFS Application Core  Orchestrates code1 (crypto), code2 (runtim` --uses--> `ProcessMonitor`  [INFERRED]
  SFFS\main-code\sffs_core.py → SFFS\code2\f10_monitor_process.py
- `f12_emergency_lock.py — Student 2: System-Security Module  The threat model: wha` --uses--> `AuditLogger`  [INFERRED]
  SFFS\code2\f12_emergency_lock.py → SFFS\code2\f11_write_audit_log.py
- `Emergency lock — immediate security lockdown.      This function performs a sequ` --uses--> `AuditLogger`  [INFERRED]
  SFFS\code2\f12_emergency_lock.py → SFFS\code2\f11_write_audit_log.py
- `Set up USB removal detection via polling.      WHY polling is used:     - Kernel` --uses--> `AuditLogger`  [INFERRED]
  SFFS\code2\f12_emergency_lock.py → SFFS\code2\f11_write_audit_log.py

## Communities

### Community 0 - "SFFSCore Orchestration"
Cohesion: 0.07
Nodes (18): checkSuspiciousProcesses(), isDebuggerPresent(), ProcessMonitor, f10_monitor_process.py — Student 2: System-Security Module  Debugger attachment, Background daemon thread that monitors for security threats.      Args:, Main monitoring loop.          Checks for debugger attachment and suspicious pro, Handle a detected threat.          Args:             threat_type: Type of threat, Stop the monitoring thread cleanly.          Sets an event to terminate the loop (+10 more)

### Community 1 - "Encryption & Decryption Pipeline"
Cohesion: 0.05
Nodes (12): encryptFile(), SFFS — Student 1: File Encryption Module  This module encrypts files using AES-2, Encrypt a file using AES-256-GCM and write to SFFS binary format.      The funct, feed_mouse_entropy(), Mouse movement entropy — mixed with OS CSPRNG for per-session file keys.  WHY: A, Call from GUI mouse-move handler; updates an internal pool (bounded)., Cryptographically strong random bytes, XOR-mixed with mouse pool if any., session_random_bytes() (+4 more)

### Community 2 - "Audit & Emergency Lock"
Cohesion: 0.07
Nodes (32): AuditLogger, _compute_entry_hash(), _getLogger(), f11_write_audit_log.py — Student 2: System-Security Module  WHY logs must be enc, Encrypt the entire database file if encryption key provided., Write a log entry.          Args:             event: Event description, Check and perform log rotation if needed., Rotate logs by deleting oldest entries.          Args:             max_entries: (+24 more)

### Community 3 - "User Authentication & Sessions"
Cohesion: 0.08
Nodes (14): apply_sffs_theme(), DragDropZone, LoginWindow, f14_ui_dashboard.py — SFFS Student 3: Main PyQt6 shell  PyQt6 provides native wi, Accepts file drops and emits the first local file path., Primary window after authentication., Collect credentials and call Student 2 ``authenticateUser``., Dark, high-contrast stylesheet for the whole application. (+6 more)

### Community 4 - "Sandbox & OS Isolation"
Cohesion: 0.1
Nodes (25): SFFS - Student 2: System-Security Module Package Functions: createIsolatedSandbo, PermissionError, _is_within(), launch_sandbox_file(), LauncherPolicyError, _load_manifest(), secure_app_launcher.py — Student 2 secure external viewer launcher.  Enforces po, Resolve and validate launch policy without starting a process.      Returns: (+17 more)

### Community 5 - "Dashboard & UI Components"
Cohesion: 0.08
Nodes (14): authenticateUser(), _compute_lock_until(), initAuthDatabase(), f09_authenticate_user.py — Student 2: System-Security Module  Argon2id is a memo, Register a new user with password hashing.      Args:         username: Username, Authenticate a user with password verification.      Args:         username: Use, Validate a session token.      Args:         session_token: Session token to val, Terminate a session by deleting it from the database.      Args:         session (+6 more)

### Community 6 - "WrapStore & Key Management"
Cohesion: 0.14
Nodes (12): _DbContext, _decrypt_blob(), _encrypt_blob(), wrap_store.py — Encrypted SQLite store for RSA-wrapped AES keys.  Replaces per-f, Store wrapped AES key keyed by SHA-256 of the .sffs file content., Return wrap_data bytes for the given .sffs file., Remove wrap entry for the given .sffs file., Decrypt .enc -> temp SQLite -> operate -> re-encrypt on exit. (+4 more)

### Community 7 - "Process & Threat Monitoring"
Cohesion: 0.12
Nodes (17): createIsolatedSandbox(), destroySandbox(), isSandboxIntact(), f07_create_isolated_sandbox.py — Student 2: System-Security Module  An isolated, Securely destroy a sandbox by wiping its contents and removing the directory., # WHY: We must wipe files before deletion because standard deletion just removes, Securely wipe all files in a directory using DOD 5220.22-M 3-pass standard., Check if a sandbox is intact and has proper security settings.      This functio (+9 more)

### Community 8 - "Cloud Sync & Config"
Cohesion: 0.16
Nodes (13): hashlib_sha256_sandwich(), SFFS — Student 1: Secure Key Storage Module  This module provides secure storage, Generate key_id from salt and iv using SHA-256 sandwich., Retrieve and decrypt an RSA private key from keystore.      Args:         keysto, Check if password can unlock keystore without exposing the key., Encrypt an AES session key using RSA-OAEP for key transport.      Args:, Unwrap an AES key that was RSA-wrapped and stored with keystore.      Args:, Securely store an RSA private key using PBKDF2 + AES-256-GCM.      Args: (+5 more)

### Community 9 - "USB & Drive Detection"
Cohesion: 0.26
Nodes (11): main(), parse_args(), run_full_app(), run_headless_demo(), run_student_demo(), run_tests(), detect_isolation(), ensure_secure_mode() (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.35
Nodes (10): _action_decrypt(), _canonical_json(), _load_policy(), main(), _policy_guard(), _purge_old_nonces(), Verify signed IPC envelope and return trusted payload., _require_not_system_path() (+2 more)

### Community 11 - "Community 11"
Cohesion: 0.36
Nodes (9): _assign_process_to_job(), _check_bool(), _create_job_object(), IO_COUNTERS, JOBOBJECT_BASIC_LIMIT_INFORMATION, JOBOBJECT_EXTENDED_LIMIT_INFORMATION, main(), If this process is not already marked as job-isolated, create a Windows Job Obje (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.36
Nodes (9): main(), _opt1(), _opt2(), _opt3(), _opt4(), _opt5(), _opt6(), _opt7() (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.29
Nodes (9): _audit(), _decode_text_preview(), _launch_with_policy(), Read-only viewer for files decrypted into the sandbox.  Text-like files are prev, Show text preview inline, or launch secure external viewer for non-text.      Re, Try decoding as common text encodings with a simple readability gate., Best-effort audit log hook through active core logger., Launch non-text files via secure app policy in code2. (+1 more)

### Community 14 - "Community 14"
Cohesion: 0.29
Nodes (6): Hardening tests for isolated worker IPC and policy checks., _sign_envelope(), test_verify_envelope_accepts_valid_signature(), test_verify_envelope_rejects_replayed_nonce(), test_verify_envelope_rejects_stale_request(), test_verify_envelope_rejects_tampered_signature()

### Community 15 - "Community 15"
Cohesion: 0.5
Nodes (1): Windows Job Object lazy activation when not started via sffs.bat.

### Community 16 - "Community 16"
Cohesion: 0.67
Nodes (1): Resolve-only integration check for portable viewers (no GUI spawn).

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (1): Pytest configuration — ensures SFFS package roots are on sys.path.

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (1): Compute canonical hash for an audit entry.

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): SFFS — Student 1: RSA Key Pair Generation Module  This module generates RSA-2048

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (1): Generate an RSA-2048 key pair for SFFS encryption/decryption.      RSA asymmetri

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (1): SecurityError

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): Exception

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (1): SFFS — Student 1: File Decryption Module  This module decrypts SFFS (.sffs) encr

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (1): Raised when a security violation is detected during decryption.

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (1): Decrypt an SFFS file and verify integrity.      The function reads the SFFS head

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (1): SFFS — Student 1: Hash Generation Module  This module provides cryptographic has

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (1): Generate a cryptographic hash of the given data.      Args:         target: Eith

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (1): Convenience function to hash a file and return metadata.      Args:         path

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (1): SFFS — Student 1: Hash Verification Module  This module verifies file integrity

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): Verify that two hashes match using constant-time comparison.      Args:

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (1): Verify integrity of a file by comparing hashes of original and decrypted version

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): Securely store an RSA private key using PBKDF2 + AES-256-GCM.      Args:

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): Generate key_id from salt and iv using SHA-256 sandwich.

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): Retrieve and decrypt an RSA private key from keystore.      Args:         keysto

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (1): Encrypt an AES session key using RSA-OAEP for key transport.      Args:

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): Unwrap an AES key that was RSA-wrapped and stored with keystore.      Args:

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (1): Check if a sandbox is intact and has proper security settings.      This functio

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): f08_secure_memory_wipe.py — Student 2: System-Security Module  Python's del keyw

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): Securely wipe sensitive data from memory using DOD 5220.22-M 3-pass standard.

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): Best-effort wipe of a string via ctypes.      WARNING: This is best-effort only.

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (1): Create a zeroed bytearray for secure data handling.      This function is intend

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (1): # WHY: ctypes is the only way in Python to directly manipulate raw memory addres

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (1): # WHY: bytearray[:] allows slice assignment with zeros

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (1): # WHY: We use bytearray for mutable overwrites

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): # WHY: This is only possible because strings are implemented as memory

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): Register a new user with password hashing.      Args:         username: Username

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): Authenticate a user with password verification.      Args:         username: Use

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (1): Validate a session token.      Args:         session_token: Session token to val

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (1): Terminate a session by deleting it from the database.      Args:         session

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (1): Main monitoring loop.          Checks for debugger attachment and suspicious pro

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (1): Handle a detected threat.          Args:             threat_type: Type of threat

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (1): Stop the monitoring thread cleanly.          Sets an event to terminate the loop

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (1): Encrypt the entire database file if encryption key provided.

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (1): Write a log entry.          Args:             event: Event description

### Community 75 - "Community 75"
Cohesion: 1.0
Nodes (1): Check and perform log rotation if needed.

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (1): Rotate logs by deleting oldest entries.          Args:             max_entries:

### Community 77 - "Community 77"
Cohesion: 1.0
Nodes (1): View recent logs.          Args:             level_filter: Optional log level fi

### Community 78 - "Community 78"
Cohesion: 1.0
Nodes (1): Verify log integrity by recomputing entry hashes.          Returns:

### Community 79 - "Community 79"
Cohesion: 1.0
Nodes (1): Get or create the global logger instance.

### Community 80 - "Community 80"
Cohesion: 1.0
Nodes (1): Write an audit log entry using the global singleton logger.      Args:         e

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (1): # WHY: Global singleton logger instance so any module can call writeAuditLog dir

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (1): Emergency lock — immediate security lockdown.      This function performs a sequ

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (1): Set up USB removal detection via polling.      WHY polling is used:     - Kernel

### Community 84 - "Community 84"
Cohesion: 1.0
Nodes (1): Set up idle timeout monitoring.      Args:         timeout_seconds: Timeout dura

### Community 85 - "Community 85"
Cohesion: 1.0
Nodes (1): Reset the idle timer on user activity.      Call this on any user action (key pr

### Community 86 - "Community 86"
Cohesion: 1.0
Nodes (1): # WHY: Closing file handles prevents attacker from accessing decrypted files

### Community 87 - "Community 87"
Cohesion: 1.0
Nodes (0): 

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (0): 

### Community 89 - "Community 89"
Cohesion: 1.0
Nodes (1): SFFS — Student 2 interactive demo runner.  Run from code2/ (imports use sibling

### Community 90 - "Community 90"
Cohesion: 1.0
Nodes (0): 

### Community 91 - "Community 91"
Cohesion: 1.0
Nodes (0): 

### Community 92 - "Community 92"
Cohesion: 1.0
Nodes (0): 

### Community 93 - "Community 93"
Cohesion: 1.0
Nodes (0): 

### Community 94 - "Community 94"
Cohesion: 1.0
Nodes (0): 

### Community 95 - "Community 95"
Cohesion: 1.0
Nodes (0): 

### Community 96 - "Community 96"
Cohesion: 1.0
Nodes (0): 

### Community 97 - "Community 97"
Cohesion: 1.0
Nodes (1): f13_init_drive_detection.py — SFFS Student 3: USB / portable path layout  Portab

### Community 98 - "Community 98"
Cohesion: 1.0
Nodes (1): Return (device, is_removable_guess, opts) for path's volume.

### Community 99 - "Community 99"
Cohesion: 1.0
Nodes (1): Return disk usage for the filesystem containing ``path``.      Args:         pat

### Community 100 - "Community 100"
Cohesion: 1.0
Nodes (1): Detect USB (or development) root and create standard SFFS directories.      Retu

### Community 101 - "Community 101"
Cohesion: 1.0
Nodes (1): Background thread: invoke ``callback`` when ``usb_root`` stops existing.      Ar

### Community 102 - "Community 102"
Cohesion: 1.0
Nodes (1): Collect credentials and call Student 2 ``authenticateUser``.

### Community 103 - "Community 103"
Cohesion: 1.0
Nodes (1): Start (or reuse) ``QApplication`` and show the main dashboard.      Args:

### Community 104 - "Community 104"
Cohesion: 1.0
Nodes (0): 

### Community 105 - "Community 105"
Cohesion: 1.0
Nodes (1): FileManagerExplorer

### Community 106 - "Community 106"
Cohesion: 1.0
Nodes (1): QWidget

### Community 107 - "Community 107"
Cohesion: 1.0
Nodes (0): 

### Community 108 - "Community 108"
Cohesion: 1.0
Nodes (0): 

### Community 109 - "Community 109"
Cohesion: 1.0
Nodes (0): 

### Community 110 - "Community 110"
Cohesion: 1.0
Nodes (0): 

### Community 111 - "Community 111"
Cohesion: 1.0
Nodes (1): f15_file_manager_explorer.py — SFFS Student 3: Scoped file browser  A host ``QFi

### Community 112 - "Community 112"
Cohesion: 1.0
Nodes (1): Two-pane explorer: directory tree + shallow file list for the selected dir.

### Community 113 - "Community 113"
Cohesion: 1.0
Nodes (1): Factory returning a configured ``FileManagerExplorer`` widget.      Args:

### Community 114 - "Community 114"
Cohesion: 1.0
Nodes (0): 

### Community 115 - "Community 115"
Cohesion: 1.0
Nodes (0): 

### Community 116 - "Community 116"
Cohesion: 1.0
Nodes (0): 

### Community 117 - "Community 117"
Cohesion: 1.0
Nodes (0): 

### Community 118 - "Community 118"
Cohesion: 1.0
Nodes (1): f16_cloud_sync.py — SFFS Student 3: Google Drive backup (optional)  OAuth 2.0 wi

### Community 119 - "Community 119"
Cohesion: 1.0
Nodes (1): Load OAuth token from ``config_dir / google_token.json`` if present.      Return

### Community 120 - "Community 120"
Cohesion: 1.0
Nodes (1): Run installed-app OAuth flow and persist token to ``google_token.json``.      Ra

### Community 121 - "Community 121"
Cohesion: 1.0
Nodes (1): Return folder ID for SFFS_Backup, creating if needed.

### Community 122 - "Community 122"
Cohesion: 1.0
Nodes (1): Upload, download, list, or delete backups on Google Drive.      Args:         ac

### Community 123 - "Community 123"
Cohesion: 1.0
Nodes (0): 

### Community 124 - "Community 124"
Cohesion: 1.0
Nodes (0): 

### Community 125 - "Community 125"
Cohesion: 1.0
Nodes (0): 

### Community 126 - "Community 126"
Cohesion: 1.0
Nodes (0): 

### Community 127 - "Community 127"
Cohesion: 1.0
Nodes (0): 

### Community 128 - "Community 128"
Cohesion: 1.0
Nodes (1): f17_config_loader.py — SFFS Student 3: Encrypted configuration  User preferences

### Community 129 - "Community 129"
Cohesion: 1.0
Nodes (1): Load, save, reset, or read a single config key.      Args:         action: ``loa

### Community 130 - "Community 130"
Cohesion: 1.0
Nodes (1): Validate config types and sensible ranges.      Returns:         ``{"valid": boo

### Community 131 - "Community 131"
Cohesion: 1.0
Nodes (1): WorkerSignals

### Community 132 - "Community 132"
Cohesion: 1.0
Nodes (1): QObject

### Community 133 - "Community 133"
Cohesion: 1.0
Nodes (1): WorkerThread

### Community 134 - "Community 134"
Cohesion: 1.0
Nodes (1): QThread

### Community 135 - "Community 135"
Cohesion: 1.0
Nodes (0): 

### Community 136 - "Community 136"
Cohesion: 1.0
Nodes (0): 

### Community 137 - "Community 137"
Cohesion: 1.0
Nodes (0): 

### Community 138 - "Community 138"
Cohesion: 1.0
Nodes (0): 

### Community 139 - "Community 139"
Cohesion: 1.0
Nodes (0): 

### Community 140 - "Community 140"
Cohesion: 1.0
Nodes (0): 

### Community 141 - "Community 141"
Cohesion: 1.0
Nodes (0): 

### Community 142 - "Community 142"
Cohesion: 1.0
Nodes (0): 

### Community 143 - "Community 143"
Cohesion: 1.0
Nodes (1): f18_thread_controller.py — SFFS Student 3: Qt worker threads  The GIL still allo

### Community 144 - "Community 144"
Cohesion: 1.0
Nodes (1): Signal bundle emitted from ``WorkerThread``.

### Community 145 - "Community 145"
Cohesion: 1.0
Nodes (1): Runs ``task(*args, **kwargs)`` and emits signals.

### Community 146 - "Community 146"
Cohesion: 1.0
Nodes (1): Start a worker thread and optionally wire callbacks.      Args:         task: Ca

### Community 147 - "Community 147"
Cohesion: 1.0
Nodes (1): Decorator: return a function that launches ``fn`` in a ``WorkerThread``.      Th

### Community 148 - "Community 148"
Cohesion: 1.0
Nodes (1): Show UTF-8 text or a hex preview for binary files.

### Community 149 - "Community 149"
Cohesion: 1.0
Nodes (0): 

### Community 150 - "Community 150"
Cohesion: 1.0
Nodes (1): SFFS setup.py — allows pip install -e . for development mode

### Community 151 - "Community 151"
Cohesion: 1.0
Nodes (1): Central orchestration for SFFS.

### Community 152 - "Community 152"
Cohesion: 1.0
Nodes (1): Decrypt if needed; reuse cached sandbox file when still present.

### Community 153 - "Community 153"
Cohesion: 1.0
Nodes (1): Decrypted files currently on disk under the session sandbox.

### Community 154 - "Community 154"
Cohesion: 1.0
Nodes (0): 

### Community 155 - "Community 155"
Cohesion: 1.0
Nodes (1): RSA Key Pair Generation

### Community 156 - "Community 156"
Cohesion: 1.0
Nodes (1): AES-GCM SFFS File Encryption

### Community 157 - "Community 157"
Cohesion: 1.0
Nodes (1): SFFS File Decryption

### Community 158 - "Community 158"
Cohesion: 1.0
Nodes (1): Streaming Hash Generation

### Community 159 - "Community 159"
Cohesion: 1.0
Nodes (1): Hash Verification

### Community 160 - "Community 160"
Cohesion: 1.0
Nodes (1): Secure Keystore and RSA Wrap

### Community 161 - "Community 161"
Cohesion: 1.0
Nodes (1): Student 1 Interactive Demo Runner

### Community 162 - "Community 162"
Cohesion: 1.0
Nodes (1): Student 1 Package Docstring

### Community 163 - "Community 163"
Cohesion: 1.0
Nodes (1): Isolated Sandbox Lifecycle

### Community 164 - "Community 164"
Cohesion: 1.0
Nodes (1): Secure Memory Wipe

### Community 165 - "Community 165"
Cohesion: 1.0
Nodes (1): Argon2id User Authentication

### Community 166 - "Community 166"
Cohesion: 1.0
Nodes (1): Debugger and Process Monitor

### Community 167 - "Community 167"
Cohesion: 1.0
Nodes (1): SQLite Audit Logger

### Community 168 - "Community 168"
Cohesion: 1.0
Nodes (1): Emergency Lock Orchestration

### Community 169 - "Community 169"
Cohesion: 1.0
Nodes (1): Student 2 Interactive Demo Runner

### Community 170 - "Community 170"
Cohesion: 1.0
Nodes (1): Student 2 Package Docstring

### Community 171 - "Community 171"
Cohesion: 1.0
Nodes (1): USB Path Map and Drive Detection

### Community 172 - "Community 172"
Cohesion: 1.0
Nodes (1): PyQt6 Dashboard and Login

### Community 173 - "Community 173"
Cohesion: 1.0
Nodes (1): Scoped QFileSystem Explorer

### Community 174 - "Community 174"
Cohesion: 1.0
Nodes (0): 

### Community 175 - "Community 175"
Cohesion: 1.0
Nodes (1): loadCredentials

### Community 176 - "Community 176"
Cohesion: 1.0
Nodes (1): authenticateGoogleDrive

### Community 177 - "Community 177"
Cohesion: 1.0
Nodes (1): _ensure_backup_folder

### Community 178 - "Community 178"
Cohesion: 1.0
Nodes (1): cloudSync

### Community 179 - "Community 179"
Cohesion: 1.0
Nodes (1): SCOPES drive.file OAuth scope

### Community 180 - "Community 180"
Cohesion: 1.0
Nodes (1): BACKUP_FOLDER_NAME SFFS_Backup

### Community 181 - "Community 181"
Cohesion: 1.0
Nodes (1): google_token.json OAuth token file

### Community 182 - "Community 182"
Cohesion: 1.0
Nodes (1): client_secret.json

### Community 183 - "Community 183"
Cohesion: 1.0
Nodes (1): Google API client libraries

### Community 184 - "Community 184"
Cohesion: 1.0
Nodes (0): 

### Community 185 - "Community 185"
Cohesion: 1.0
Nodes (1): configLoader

### Community 186 - "Community 186"
Cohesion: 1.0
Nodes (1): validateConfig

### Community 187 - "Community 187"
Cohesion: 1.0
Nodes (1): _encrypt_blob

### Community 188 - "Community 188"
Cohesion: 1.0
Nodes (1): _decrypt_blob

### Community 189 - "Community 189"
Cohesion: 1.0
Nodes (1): DEFAULT_CONFIG schema

### Community 190 - "Community 190"
Cohesion: 1.0
Nodes (1): sffs_config.enc encrypted config

### Community 191 - "Community 191"
Cohesion: 1.0
Nodes (1): sffs_config.json plain dev config

### Community 192 - "Community 192"
Cohesion: 1.0
Nodes (1): AES-GCM for config at rest

### Community 193 - "Community 193"
Cohesion: 1.0
Nodes (0): 

### Community 194 - "Community 194"
Cohesion: 1.0
Nodes (1): WorkerSignals

### Community 195 - "Community 195"
Cohesion: 1.0
Nodes (1): WorkerThread

### Community 196 - "Community 196"
Cohesion: 1.0
Nodes (1): threadController

### Community 197 - "Community 197"
Cohesion: 1.0
Nodes (1): run_in_thread decorator

### Community 198 - "Community 198"
Cohesion: 1.0
Nodes (1): PyQt6 QThread pyqtSignal

### Community 199 - "Community 199"
Cohesion: 1.0
Nodes (1): Qt GUI updates must run on main thread

### Community 200 - "Community 200"
Cohesion: 1.0
Nodes (0): 

### Community 201 - "Community 201"
Cohesion: 1.0
Nodes (1): feed_mouse_entropy

### Community 202 - "Community 202"
Cohesion: 1.0
Nodes (1): session_random_bytes

### Community 203 - "Community 203"
Cohesion: 1.0
Nodes (1): secrets.token_bytes CSPRNG

### Community 204 - "Community 204"
Cohesion: 1.0
Nodes (0): 

### Community 205 - "Community 205"
Cohesion: 1.0
Nodes (1): main interactive demo runner

### Community 206 - "Community 206"
Cohesion: 1.0
Nodes (0): 

### Community 207 - "Community 207"
Cohesion: 1.0
Nodes (1): show_sandbox_file_viewer

### Community 208 - "Community 208"
Cohesion: 1.0
Nodes (1): code3/__init__.py

### Community 209 - "Community 209"
Cohesion: 1.0
Nodes (0): 

### Community 210 - "Community 210"
Cohesion: 1.0
Nodes (1): parse_args

### Community 211 - "Community 211"
Cohesion: 1.0
Nodes (1): run_tests

### Community 212 - "Community 212"
Cohesion: 1.0
Nodes (1): run_student_demo

### Community 213 - "Community 213"
Cohesion: 1.0
Nodes (1): run_headless_demo

### Community 214 - "Community 214"
Cohesion: 1.0
Nodes (1): run_full_app

### Community 215 - "Community 215"
Cohesion: 1.0
Nodes (1): main

### Community 216 - "Community 216"
Cohesion: 1.0
Nodes (0): 

### Community 217 - "Community 217"
Cohesion: 1.0
Nodes (1): sffs setuptools package

### Community 218 - "Community 218"
Cohesion: 1.0
Nodes (1): Ibraheem Snineh

### Community 219 - "Community 219"
Cohesion: 1.0
Nodes (1): Karim Taha

### Community 220 - "Community 220"
Cohesion: 1.0
Nodes (1): Mazin Alsarahin

### Community 221 - "Community 221"
Cohesion: 1.0
Nodes (0): 

### Community 222 - "Community 222"
Cohesion: 1.0
Nodes (1): SFFSCore

### Community 223 - "Community 223"
Cohesion: 1.0
Nodes (1): SFFSCore.initialize

### Community 224 - "Community 224"
Cohesion: 1.0
Nodes (1): SFFSCore.login

### Community 225 - "Community 225"
Cohesion: 1.0
Nodes (1): SFFSCore.encryptFileOperation

### Community 226 - "Community 226"
Cohesion: 1.0
Nodes (1): SFFSCore.decryptFileOperation

### Community 227 - "Community 227"
Cohesion: 1.0
Nodes (1): SFFSCore.backupKeys

### Community 228 - "Community 228"
Cohesion: 1.0
Nodes (1): sffs_keys_backup.zip

### Community 229 - "Community 229"
Cohesion: 1.0
Nodes (1): main-code/__init__.py

### Community 230 - "Community 230"
Cohesion: 1.0
Nodes (1): tests/conftest.py

### Community 231 - "Community 231"
Cohesion: 1.0
Nodes (1): tests/test_student1.py

### Community 232 - "Community 232"
Cohesion: 1.0
Nodes (1): tests/test_student2.py

### Community 233 - "Community 233"
Cohesion: 1.0
Nodes (1): tests/test_student3.py

### Community 234 - "Community 234"
Cohesion: 1.0
Nodes (1): tests/__init__.py

### Community 235 - "Community 235"
Cohesion: 1.0
Nodes (1): test_cloud_sync_encrypts_before_upload skipped

### Community 236 - "Community 236"
Cohesion: 1.0
Nodes (0): 

### Community 237 - "Community 237"
Cohesion: 1.0
Nodes (1): p00_scaffold.md Phase 0

### Community 238 - "Community 238"
Cohesion: 1.0
Nodes (1): p01_student1.md Phase 1 crypto

### Community 239 - "Community 239"
Cohesion: 1.0
Nodes (1): p02_student2.md Phase 2 runtime security

### Community 240 - "Community 240"
Cohesion: 1.0
Nodes (1): p03_student3.md Phase 3 architect

### Community 241 - "Community 241"
Cohesion: 1.0
Nodes (0): 

### Community 242 - "Community 242"
Cohesion: 1.0
Nodes (0): 

### Community 243 - "Community 243"
Cohesion: 1.0
Nodes (0): 

### Community 244 - "Community 244"
Cohesion: 1.0
Nodes (0): 

### Community 245 - "Community 245"
Cohesion: 1.0
Nodes (1): Smart File Fortify System SFFS

### Community 246 - "Community 246"
Cohesion: 1.0
Nodes (1): .sffs custom binary format

### Community 247 - "Community 247"
Cohesion: 1.0
Nodes (1): AES-256-GCM file encryption

### Community 248 - "Community 248"
Cohesion: 1.0
Nodes (1): RSA-2048 key management

### Community 249 - "Community 249"
Cohesion: 1.0
Nodes (1): Argon2id password hashing

### Community 250 - "Community 250"
Cohesion: 1.0
Nodes (1): PBKDF2-SHA256 310000 iterations

### Community 251 - "Community 251"
Cohesion: 1.0
Nodes (1): https://www.python.org/downloads/

### Community 252 - "Community 252"
Cohesion: 1.0
Nodes (1): https://console.cloud.google.com/

### Community 253 - "Community 253"
Cohesion: 1.0
Nodes (1): OWASP 2023 recommendations cited in specs

### Community 254 - "Community 254"
Cohesion: 1.0
Nodes (1): NIST 2023 PBKDF2 iteration guidance cited

### Community 255 - "Community 255"
Cohesion: 1.0
Nodes (1): console_scripts entry sffs=main-code.main:main may be invalid for setuptools

### Community 256 - "Community 256"
Cohesion: 1.0
Nodes (1): CLAUDE claims non-software directory vs implemented Python project

### Community 257 - "Community 257"
Cohesion: 1.0
Nodes (1): SFFS master build plan: phases, checkpoints, directory layout, dependency matrix

### Community 258 - "Community 258"
Cohesion: 1.0
Nodes (1): Root Python dependency pin (cryptography)

### Community 259 - "Community 259"
Cohesion: 1.0
Nodes (1): Student 1 crypto module README: AES-256-GCM, .sffs format, PBKDF2 demo

### Community 260 - "Community 260"
Cohesion: 1.0
Nodes (1): Plaintext fixture: Hello SFFS test file

### Community 261 - "Community 261"
Cohesion: 1.0
Nodes (1): Student 2 system security README: sandbox, Argon2id, audit log, emergency lock

### Community 262 - "Community 262"
Cohesion: 1.0
Nodes (1): Student 3 architect README: USB paths, PyQt6 UI, Google Drive, threads

### Community 263 - "Community 263"
Cohesion: 1.0
Nodes (1): API reference for F-01 through F-18 and SFFSCore integration

### Community 264 - "Community 264"
Cohesion: 1.0
Nodes (1): SFFS architecture: module map, init sequence, encrypt/decrypt flows, .sffs layout

### Community 265 - "Community 265"
Cohesion: 1.0
Nodes (1): Developer setup, structure, extension rules, pytest commands

### Community 266 - "Community 266"
Cohesion: 1.0
Nodes (1): Threat model, crypto choices, mitigations, known limitations

### Community 267 - "Community 267"
Cohesion: 1.0
Nodes (1): USB install guide: copy tree, sffs.bat/sffs.sh, verify, Drive OAuth

### Community 268 - "Community 268"
Cohesion: 1.0
Nodes (1): Main application README: quick start, SFFSCore orchestration, security summary

### Community 269 - "Community 269"
Cohesion: 1.0
Nodes (1): Pinned stack: pycryptodome, cryptography, argon2-cffi, psutil, PyQt6, Google APIs

### Community 270 - "Community 270"
Cohesion: 1.0
Nodes (1): GP1mk2 slide deck: SFFS background, comparison table, objectives, methodology, UML narrative

### Community 271 - "Community 271"
Cohesion: 1.0
Nodes (1): AES-256-GCM authenticated encryption for files at rest

### Community 272 - "Community 272"
Cohesion: 1.0
Nodes (1): RSA-2048 OAEP wrapping of per-file AES keys (.aeswrap)

### Community 273 - "Community 273"
Cohesion: 1.0
Nodes (1): SHA-256 plaintext fingerprints and verifyHash comparisons

### Community 274 - "Community 274"
Cohesion: 1.0
Nodes (1): .sffs binary container: magic, version, IV, tag, hash_pre, size, ciphertext

### Community 275 - "Community 275"
Cohesion: 1.0
Nodes (1): Argon2id password hashing and SQLite-backed sessions (F-09)

### Community 276 - "Community 276"
Cohesion: 1.0
Nodes (1): PBKDF2-SHA256-derived key encrypting RSA private material in keystore JSON

### Community 277 - "Community 277"
Cohesion: 1.0
Nodes (1): USB-relative paths, session sandbox, decrypted_dir on removable media

### Community 278 - "Community 278"
Cohesion: 1.0
Nodes (1): SFFSCore orchestrator in main-code/sffs_core.py wiring students 1-3

### Community 279 - "Community 279"
Cohesion: 1.0
Nodes (1): SQLite audit trail and writeAuditLog singleton patterns

### Community 280 - "Community 280"
Cohesion: 1.0
Nodes (1): Optional Google Drive OAuth upload of already-encrypted material

### Community 281 - "Community 281"
Cohesion: 1.0
Nodes (1): USB removal/debug triggers emergencyLock, sandbox teardown, session end

### Community 282 - "Community 282"
Cohesion: 1.0
Nodes (1): Debugger/suspicious-process heuristics and ProcessMonitor daemon

### Community 283 - "Community 283"
Cohesion: 1.0
Nodes (1): PyQt6 dashboard, login window, worker threads for crypto/file IO

### Community 284 - "Community 284"
Cohesion: 1.0
Nodes (1): EncryptionEngine class handling AES/RSA (conceptual UML)

### Community 285 - "Community 285"
Cohesion: 1.0
Nodes (1): KeyManager class for secure key lifecycle (conceptual UML)

### Community 286 - "Community 286"
Cohesion: 1.0
Nodes (1): IsolatedEnvironment sandbox class isolating file ops (conceptual UML)

### Community 287 - "Community 287"
Cohesion: 1.0
Nodes (1): FileManager class coordinating UI file operations (conceptual UML)

### Community 288 - "Community 288"
Cohesion: 1.0
Nodes (1): Multi-factor authentication stated as future/user-centric objective

## Knowledge Gaps
- **273 isolated node(s):** `SFFS — Student 1: File Encryption Module  This module encrypts files using AES-2`, `Encrypt a file using AES-256-GCM and write to SFFS binary format.      The funct`, `SFFS — Student 1: Secure Key Storage Module  This module provides secure storage`, `Securely store an RSA private key using PBKDF2 + AES-256-GCM.      Args:`, `Generate key_id from salt and iv using SHA-256 sandwich.` (+268 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 17`** (2 nodes): `conftest.py`, `Pytest configuration — ensures SFFS package roots are on sys.path.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `Compute canonical hash for an audit entry.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `fetch_missing_viewers.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `reset_sffs_data.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `_rm()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `sffs_install_deps.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `sffs_usb_setup.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `list_removable()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `verify()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `install_deps()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `generateKeyPairs()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `SFFS — Student 1: RSA Key Pair Generation Module  This module generates RSA-2048`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `Generate an RSA-2048 key pair for SFFS encryption/decryption.      RSA asymmetri`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `SecurityError`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `Exception`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `decryptFile()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `SFFS — Student 1: File Decryption Module  This module decrypts SFFS (.sffs) encr`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `Raised when a security violation is detected during decryption.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `Decrypt an SFFS file and verify integrity.      The function reads the SFFS head`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `generateHash()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `generateFileHash()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `SFFS — Student 1: Hash Generation Module  This module provides cryptographic has`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `Generate a cryptographic hash of the given data.      Args:         target: Eith`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `Convenience function to hash a file and return metadata.      Args:         path`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `verifyHash()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `verifyFileIntegrity()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `SFFS — Student 1: Hash Verification Module  This module verifies file integrity`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `Verify that two hashes match using constant-time comparison.      Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `Verify integrity of a file by comparing hashes of original and decrypted version`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `Securely store an RSA private key using PBKDF2 + AES-256-GCM.      Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `Generate key_id from salt and iv using SHA-256 sandwich.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `Retrieve and decrypt an RSA private key from keystore.      Args:         keysto`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `Encrypt an AES session key using RSA-OAEP for key transport.      Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `Unwrap an AES key that was RSA-wrapped and stored with keystore.      Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `Check if a sandbox is intact and has proper security settings.      This functio`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `secureMemoryWipe()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `wipeString()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `createSecureBuffer()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `f08_secure_memory_wipe.py — Student 2: System-Security Module  Python's del keyw`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `Securely wipe sensitive data from memory using DOD 5220.22-M 3-pass standard.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `Best-effort wipe of a string via ctypes.      WARNING: This is best-effort only.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `Create a zeroed bytearray for secure data handling.      This function is intend`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `# WHY: ctypes is the only way in Python to directly manipulate raw memory addres`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `# WHY: bytearray[:] allows slice assignment with zeros`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `# WHY: We use bytearray for mutable overwrites`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `# WHY: This is only possible because strings are implemented as memory`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `Register a new user with password hashing.      Args:         username: Username`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `Authenticate a user with password verification.      Args:         username: Use`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `Validate a session token.      Args:         session_token: Session token to val`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `Terminate a session by deleting it from the database.      Args:         session`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `Main monitoring loop.          Checks for debugger attachment and suspicious pro`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `Handle a detected threat.          Args:             threat_type: Type of threat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `Stop the monitoring thread cleanly.          Sets an event to terminate the loop`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `Encrypt the entire database file if encryption key provided.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `Write a log entry.          Args:             event: Event description`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (1 nodes): `Check and perform log rotation if needed.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 76`** (1 nodes): `Rotate logs by deleting oldest entries.          Args:             max_entries:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 77`** (1 nodes): `View recent logs.          Args:             level_filter: Optional log level fi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 78`** (1 nodes): `Verify log integrity by recomputing entry hashes.          Returns:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 79`** (1 nodes): `Get or create the global logger instance.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 80`** (1 nodes): `Write an audit log entry using the global singleton logger.      Args:         e`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 81`** (1 nodes): `# WHY: Global singleton logger instance so any module can call writeAuditLog dir`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `Emergency lock — immediate security lockdown.      This function performs a sequ`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (1 nodes): `Set up USB removal detection via polling.      WHY polling is used:     - Kernel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 84`** (1 nodes): `Set up idle timeout monitoring.      Args:         timeout_seconds: Timeout dura`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 85`** (1 nodes): `Reset the idle timer on user activity.      Call this on any user action (key pr`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 86`** (1 nodes): `# WHY: Closing file handles prevents attacker from accessing decrypted files`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 87`** (1 nodes): `run_student2.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (1 nodes): `_menu()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 89`** (1 nodes): `SFFS — Student 2 interactive demo runner.  Run from code2/ (imports use sibling`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 90`** (1 nodes): `_resolved_script_parent()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 91`** (1 nodes): `_windows_volume_root()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 92`** (1 nodes): `_linux_mount_root()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 93`** (1 nodes): `_partition_for_path()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 94`** (1 nodes): `getAvailableSpace()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 95`** (1 nodes): `initDriveDetection()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 96`** (1 nodes): `monitorUSBPresence()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 97`** (1 nodes): `f13_init_drive_detection.py — SFFS Student 3: USB / portable path layout  Portab`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 98`** (1 nodes): `Return (device, is_removable_guess, opts) for path's volume.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 99`** (1 nodes): `Return disk usage for the filesystem containing ``path``.      Args:         pat`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 100`** (1 nodes): `Detect USB (or development) root and create standard SFFS directories.      Retu`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 101`** (1 nodes): `Background thread: invoke ``callback`` when ``usb_root`` stops existing.      Ar`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 102`** (1 nodes): `Collect credentials and call Student 2 ``authenticateUser``.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 103`** (1 nodes): `Start (or reuse) ``QApplication`` and show the main dashboard.      Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 104`** (1 nodes): `f15_file_manager_explorer.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 105`** (1 nodes): `FileManagerExplorer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 106`** (1 nodes): `QWidget`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 107`** (1 nodes): `.__init__()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 108`** (1 nodes): `._on_tree_change()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 109`** (1 nodes): `._on_double_click()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 110`** (1 nodes): `._ctx_menu()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 111`** (1 nodes): `f15_file_manager_explorer.py — SFFS Student 3: Scoped file browser  A host ``QFi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 112`** (1 nodes): `Two-pane explorer: directory tree + shallow file list for the selected dir.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 113`** (1 nodes): `Factory returning a configured ``FileManagerExplorer`` widget.      Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 114`** (1 nodes): `loadCredentials()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 115`** (1 nodes): `authenticateGoogleDrive()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 116`** (1 nodes): `_ensure_backup_folder()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 117`** (1 nodes): `cloudSync()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 118`** (1 nodes): `f16_cloud_sync.py — SFFS Student 3: Google Drive backup (optional)  OAuth 2.0 wi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 119`** (1 nodes): `Load OAuth token from ``config_dir / google_token.json`` if present.      Return`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 120`** (1 nodes): `Run installed-app OAuth flow and persist token to ``google_token.json``.      Ra`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 121`** (1 nodes): `Return folder ID for SFFS_Backup, creating if needed.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 122`** (1 nodes): `Upload, download, list, or delete backups on Google Drive.      Args:         ac`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 123`** (1 nodes): `_merge_defaults()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 124`** (1 nodes): `_encrypt_blob()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 125`** (1 nodes): `_decrypt_blob()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 126`** (1 nodes): `configLoader()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 127`** (1 nodes): `validateConfig()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 128`** (1 nodes): `f17_config_loader.py — SFFS Student 3: Encrypted configuration  User preferences`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 129`** (1 nodes): `Load, save, reset, or read a single config key.      Args:         action: ``loa`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 130`** (1 nodes): `Validate config types and sensible ranges.      Returns:         ``{"valid": boo`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 131`** (1 nodes): `WorkerSignals`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 132`** (1 nodes): `QObject`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 133`** (1 nodes): `WorkerThread`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 134`** (1 nodes): `QThread`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 135`** (1 nodes): `.__init__()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 136`** (1 nodes): `.cancel()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 137`** (1 nodes): `.is_cancelled()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 138`** (1 nodes): `.run()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 139`** (1 nodes): `threadController()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 140`** (1 nodes): `run_in_thread()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 141`** (1 nodes): `task_with_progress()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 142`** (1 nodes): `on_prog()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 143`** (1 nodes): `f18_thread_controller.py — SFFS Student 3: Qt worker threads  The GIL still allo`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 144`** (1 nodes): `Signal bundle emitted from ``WorkerThread``.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 145`** (1 nodes): `Runs ``task(*args, **kwargs)`` and emits signals.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 146`** (1 nodes): `Start a worker thread and optionally wire callbacks.      Args:         task: Ca`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 147`** (1 nodes): `Decorator: return a function that launches ``fn`` in a ``WorkerThread``.      Th`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 148`** (1 nodes): `Show UTF-8 text or a hex preview for binary files.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 149`** (1 nodes): `setup.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 150`** (1 nodes): `SFFS setup.py — allows pip install -e . for development mode`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 151`** (1 nodes): `Central orchestration for SFFS.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 152`** (1 nodes): `Decrypt if needed; reuse cached sandbox file when still present.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 153`** (1 nodes): `Decrypted files currently on disk under the session sandbox.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 154`** (1 nodes): `test_cloud_sync_encrypts_before_upload()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 155`** (1 nodes): `RSA Key Pair Generation`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 156`** (1 nodes): `AES-GCM SFFS File Encryption`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 157`** (1 nodes): `SFFS File Decryption`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 158`** (1 nodes): `Streaming Hash Generation`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 159`** (1 nodes): `Hash Verification`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 160`** (1 nodes): `Secure Keystore and RSA Wrap`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 161`** (1 nodes): `Student 1 Interactive Demo Runner`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 162`** (1 nodes): `Student 1 Package Docstring`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 163`** (1 nodes): `Isolated Sandbox Lifecycle`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 164`** (1 nodes): `Secure Memory Wipe`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 165`** (1 nodes): `Argon2id User Authentication`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 166`** (1 nodes): `Debugger and Process Monitor`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 167`** (1 nodes): `SQLite Audit Logger`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 168`** (1 nodes): `Emergency Lock Orchestration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 169`** (1 nodes): `Student 2 Interactive Demo Runner`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 170`** (1 nodes): `Student 2 Package Docstring`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 171`** (1 nodes): `USB Path Map and Drive Detection`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 172`** (1 nodes): `PyQt6 Dashboard and Login`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 173`** (1 nodes): `Scoped QFileSystem Explorer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 174`** (1 nodes): `f16_cloud_sync.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 175`** (1 nodes): `loadCredentials`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 176`** (1 nodes): `authenticateGoogleDrive`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 177`** (1 nodes): `_ensure_backup_folder`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 178`** (1 nodes): `cloudSync`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 179`** (1 nodes): `SCOPES drive.file OAuth scope`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 180`** (1 nodes): `BACKUP_FOLDER_NAME SFFS_Backup`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 181`** (1 nodes): `google_token.json OAuth token file`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 182`** (1 nodes): `client_secret.json`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 183`** (1 nodes): `Google API client libraries`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 184`** (1 nodes): `f17_config_loader.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 185`** (1 nodes): `configLoader`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 186`** (1 nodes): `validateConfig`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 187`** (1 nodes): `_encrypt_blob`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 188`** (1 nodes): `_decrypt_blob`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 189`** (1 nodes): `DEFAULT_CONFIG schema`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 190`** (1 nodes): `sffs_config.enc encrypted config`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 191`** (1 nodes): `sffs_config.json plain dev config`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 192`** (1 nodes): `AES-GCM for config at rest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 193`** (1 nodes): `f18_thread_controller.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 194`** (1 nodes): `WorkerSignals`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 195`** (1 nodes): `WorkerThread`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 196`** (1 nodes): `threadController`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 197`** (1 nodes): `run_in_thread decorator`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 198`** (1 nodes): `PyQt6 QThread pyqtSignal`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 199`** (1 nodes): `Qt GUI updates must run on main thread`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 200`** (1 nodes): `mouse_entropy.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 201`** (1 nodes): `feed_mouse_entropy`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 202`** (1 nodes): `session_random_bytes`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 203`** (1 nodes): `secrets.token_bytes CSPRNG`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 204`** (1 nodes): `run_student3.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 205`** (1 nodes): `main interactive demo runner`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 206`** (1 nodes): `sandbox_viewer.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 207`** (1 nodes): `show_sandbox_file_viewer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 208`** (1 nodes): `code3/__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 209`** (1 nodes): `main.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 210`** (1 nodes): `parse_args`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 211`** (1 nodes): `run_tests`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 212`** (1 nodes): `run_student_demo`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 213`** (1 nodes): `run_headless_demo`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 214`** (1 nodes): `run_full_app`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 215`** (1 nodes): `main`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 216`** (1 nodes): `setup.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 217`** (1 nodes): `sffs setuptools package`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 218`** (1 nodes): `Ibraheem Snineh`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 219`** (1 nodes): `Karim Taha`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 220`** (1 nodes): `Mazin Alsarahin`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 221`** (1 nodes): `sffs_core.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 222`** (1 nodes): `SFFSCore`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 223`** (1 nodes): `SFFSCore.initialize`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 224`** (1 nodes): `SFFSCore.login`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 225`** (1 nodes): `SFFSCore.encryptFileOperation`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 226`** (1 nodes): `SFFSCore.decryptFileOperation`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 227`** (1 nodes): `SFFSCore.backupKeys`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 228`** (1 nodes): `sffs_keys_backup.zip`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 229`** (1 nodes): `main-code/__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 230`** (1 nodes): `tests/conftest.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 231`** (1 nodes): `tests/test_student1.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 232`** (1 nodes): `tests/test_student2.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 233`** (1 nodes): `tests/test_student3.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 234`** (1 nodes): `tests/__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 235`** (1 nodes): `test_cloud_sync_encrypts_before_upload skipped`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 236`** (1 nodes): `CLAUDE.md`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 237`** (1 nodes): `p00_scaffold.md Phase 0`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 238`** (1 nodes): `p01_student1.md Phase 1 crypto`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 239`** (1 nodes): `p02_student2.md Phase 2 runtime security`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 240`** (1 nodes): `p03_student3.md Phase 3 architect`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 241`** (1 nodes): `p04_main_integration.md`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 242`** (1 nodes): `p05_runners.md`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 243`** (1 nodes): `p06_docs.md`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 244`** (1 nodes): `p07_usb_install.md`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 245`** (1 nodes): `Smart File Fortify System SFFS`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 246`** (1 nodes): `.sffs custom binary format`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 247`** (1 nodes): `AES-256-GCM file encryption`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 248`** (1 nodes): `RSA-2048 key management`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 249`** (1 nodes): `Argon2id password hashing`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 250`** (1 nodes): `PBKDF2-SHA256 310000 iterations`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 251`** (1 nodes): `https://www.python.org/downloads/`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 252`** (1 nodes): `https://console.cloud.google.com/`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 253`** (1 nodes): `OWASP 2023 recommendations cited in specs`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 254`** (1 nodes): `NIST 2023 PBKDF2 iteration guidance cited`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 255`** (1 nodes): `console_scripts entry sffs=main-code.main:main may be invalid for setuptools`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 256`** (1 nodes): `CLAUDE claims non-software directory vs implemented Python project`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 257`** (1 nodes): `SFFS master build plan: phases, checkpoints, directory layout, dependency matrix`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 258`** (1 nodes): `Root Python dependency pin (cryptography)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 259`** (1 nodes): `Student 1 crypto module README: AES-256-GCM, .sffs format, PBKDF2 demo`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 260`** (1 nodes): `Plaintext fixture: Hello SFFS test file`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 261`** (1 nodes): `Student 2 system security README: sandbox, Argon2id, audit log, emergency lock`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 262`** (1 nodes): `Student 3 architect README: USB paths, PyQt6 UI, Google Drive, threads`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 263`** (1 nodes): `API reference for F-01 through F-18 and SFFSCore integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 264`** (1 nodes): `SFFS architecture: module map, init sequence, encrypt/decrypt flows, .sffs layout`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 265`** (1 nodes): `Developer setup, structure, extension rules, pytest commands`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 266`** (1 nodes): `Threat model, crypto choices, mitigations, known limitations`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 267`** (1 nodes): `USB install guide: copy tree, sffs.bat/sffs.sh, verify, Drive OAuth`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 268`** (1 nodes): `Main application README: quick start, SFFSCore orchestration, security summary`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 269`** (1 nodes): `Pinned stack: pycryptodome, cryptography, argon2-cffi, psutil, PyQt6, Google APIs`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 270`** (1 nodes): `GP1mk2 slide deck: SFFS background, comparison table, objectives, methodology, UML narrative`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 271`** (1 nodes): `AES-256-GCM authenticated encryption for files at rest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 272`** (1 nodes): `RSA-2048 OAEP wrapping of per-file AES keys (.aeswrap)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 273`** (1 nodes): `SHA-256 plaintext fingerprints and verifyHash comparisons`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 274`** (1 nodes): `.sffs binary container: magic, version, IV, tag, hash_pre, size, ciphertext`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 275`** (1 nodes): `Argon2id password hashing and SQLite-backed sessions (F-09)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 276`** (1 nodes): `PBKDF2-SHA256-derived key encrypting RSA private material in keystore JSON`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 277`** (1 nodes): `USB-relative paths, session sandbox, decrypted_dir on removable media`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 278`** (1 nodes): `SFFSCore orchestrator in main-code/sffs_core.py wiring students 1-3`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 279`** (1 nodes): `SQLite audit trail and writeAuditLog singleton patterns`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 280`** (1 nodes): `Optional Google Drive OAuth upload of already-encrypted material`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 281`** (1 nodes): `USB removal/debug triggers emergencyLock, sandbox teardown, session end`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 282`** (1 nodes): `Debugger/suspicious-process heuristics and ProcessMonitor daemon`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 283`** (1 nodes): `PyQt6 dashboard, login window, worker threads for crypto/file IO`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 284`** (1 nodes): `EncryptionEngine class handling AES/RSA (conceptual UML)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 285`** (1 nodes): `KeyManager class for secure key lifecycle (conceptual UML)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 286`** (1 nodes): `IsolatedEnvironment sandbox class isolating file ops (conceptual UML)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 287`** (1 nodes): `FileManager class coordinating UI file operations (conceptual UML)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 288`** (1 nodes): `Multi-factor authentication stated as future/user-centric objective`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SFFSCore` connect `SFFSCore Orchestration` to `Encryption & Decryption Pipeline`, `Audit & Emergency Lock`, `Sandbox & OS Isolation`, `WrapStore & Key Management`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `AuditLogger` connect `Audit & Emergency Lock` to `SFFSCore Orchestration`, `Encryption & Decryption Pipeline`, `Dashboard & UI Components`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `WrapStore` connect `WrapStore & Key Management` to `SFFSCore Orchestration`, `Encryption & Decryption Pipeline`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `AuditLogger` (e.g. with `f12_emergency_lock.py — Student 2: System-Security Module  The threat model: wha` and `Emergency lock — immediate security lockdown.      This function performs a sequ`) actually correct?**
  _`AuditLogger` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `SFFSCore` (e.g. with `WrapStore` and `ProcessMonitor`) actually correct?**
  _`SFFSCore` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `WrapStore` (e.g. with `SFFSCore` and `sffs_core.py — SFFS Application Core  Orchestrates code1 (crypto), code2 (runtim`) actually correct?**
  _`WrapStore` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `ProcessMonitor` (e.g. with `SFFSCore` and `sffs_core.py — SFFS Application Core  Orchestrates code1 (crypto), code2 (runtim`) actually correct?**
  _`ProcessMonitor` has 8 INFERRED edges - model-reasoned connections that need verification._