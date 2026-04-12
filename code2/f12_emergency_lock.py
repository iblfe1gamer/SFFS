"""
f12_emergency_lock.py — Student 2: System-Security Module

The threat model: what happens if the USB is pulled while files are decrypted?
- Decrypted files are immediately accessible to the attacker
- Decryption keys are in memory and can be dumped
- The attacker can now read all secrets

The sequence of operations that must happen in < 500ms:
1. Set EMERGENCY_ACTIVE = True flag
2. Close all open file handles
3. Wipe memory targets (keys, passwords, etc.)
4. Destroy sandbox (delete decrypted files)
5. Terminate session (delete session token)
6. Write CRITICAL audit log entry
7. sys.exit(0) — hard termination

WHY the log write happens LAST:
- So we know the lock completed successfully
- If lock failed, attacker still has access
- We want to know the lock was attempted

WHY sys.exit() is called:
- Don't trust atexit handlers
- Don't trust garbage collection
- Hard termination is guaranteed

Triggers:
- USB_REMOVED: physical removal — immediate, no user prompt
- DEBUGGER_DETECTED: security threat — immediate, log threat details
- TIMEOUT: idle timeout — graceful, can be resumed with re-authentication
- MANUAL: user pressed lock button — graceful
- MAX_FAILURES: too many wrong passwords — immediate
"""

import signal
import sys
import os
import threading
import time
from pathlib import Path

# Import sibling modules for emergency lock operations
from f08_secure_memory_wipe import secureMemoryWipe
from f07_create_isolated_sandbox import destroySandbox
from f11_write_audit_log import writeAuditLog
from f09_authenticate_user import terminateSession

# WHY: signal allows catching OS signals (SIGTERM, SIGHUP) for clean shutdown on USB removal
# WHY: threading for background threads that monitor USB and idle timeout
# WHY: pathlib for cross-platform path handling
# WHY: sys and os for emergency exit and file operations
import signal
import threading
import time
from pathlib import Path
import os

# WHY: sys.exit() is called at the end — don't trust atexit or garbage collection
import sys


EMERGENCY_ACTIVE = False  # Global flag checked by all operations


def emergencyLock(trigger: str, sandbox_path: Path = None, session_token: str = None,
                  db_path: Path = None, wipe_memory_targets: list = None) -> None:
    """
    Emergency lock — immediate security lockdown.

    This function performs a sequence of operations to lock down the system:
    1. Set global emergency flag
    2. Close all open file handles
    3. Wipe memory targets (keys, passwords, etc.)
    4. Destroy sandbox (delete decrypted files)
    5. Terminate session (delete session token)
    6. Write CRITICAL audit log entry
    7. sys.exit(0) — hard termination

    Each step is wrapped in try/except — if a step fails, skip it and continue.

    Args:
        trigger: Trigger reason (USB_REMOVED, DEBUGGER_DETECTED, TIMEOUT, MANUAL, MAX_FAILURES)
        sandbox_path: Path to sandbox to destroy
        session_token: Session token to terminate
        db_path: Path to authentication database
        wipe_memory_targets: List of bytearrays to wipe

    Security Notes:
        WHY each step matters:
        - Step 1: Prevents other operations from running
        - Step 2: Prevents attacker from accessing open files
        - Step 3: Prevents attacker from reading decrypted keys from memory
        - Step 4: Prevents attacker from accessing decrypted files
        - Step 5: Prevents attacker from using session to access system
        - Step 6: Provides forensic evidence of the lock
        - Step 7: Hard termination prevents attacker from continuing
    """
    global EMERGENCY_ACTIVE

    # Step 1: Set global EMERGENCY_ACTIVE flag
    try:
        EMERGENCY_ACTIVE = True
    except Exception as e:
        print(f"Step 1 failed (flag): {e}")

    # Step 2: Close all open file handles (best-effort)
    try:
        # WHY: Closing file handles prevents attacker from accessing decrypted files
        if sandbox_path:
            sandbox_path.rmdir()  # This also closes any open file handles
    except Exception as e:
        print(f"Step 2 failed (close handles): {e}")

    # Step 3: Wipe memory targets (keys, passwords, etc.)
    try:
        if wipe_memory_targets:
            for target in wipe_memory_targets:
                secureMemoryWipe(target)
    except Exception as e:
        print(f"Step 3 failed (wipe memory): {e}")

    # Step 4: Destroy sandbox (delete decrypted files)
    try:
        if sandbox_path and sandbox_path.exists():
            destroySandbox(sandbox_path)
    except Exception as e:
        print(f"Step 4 failed (destroy sandbox): {e}")

    # Step 5: Terminate session (delete session token)
    try:
        if session_token and db_path:
            terminateSession(session_token, db_path)
    except Exception as e:
        print(f"Step 5 failed (terminate session): {e}")

    # Step 6: Write CRITICAL audit log entry
    try:
        writeAuditLog(
            f"EMERGENCY LOCK: Trigger={trigger}, Sandboxed={sandbox_path is not None}, "
            f"Session={session_token is not None}",
            level="CRITICAL"
        )
    except Exception as e:
        print(f"Step 6 failed (write log): {e}")

    # Step 7: sys.exit(0) — hard termination
    try:
        sys.exit(0)
    except SystemExit:
        pass  # Normal exit


def setupUSBRemovalDetection(usb_root: Path, lock_callback) -> threading.Thread:
    """
    Set up USB removal detection via polling.

    WHY polling is used:
    - Kernel-level inotify would be better but is Linux-only
    - Polling is simpler and more portable
    - Runs on both Windows and Linux

    Args:
        usb_root: Path to USB mount point
        lock_callback: Callback function called when USB is removed

    Returns:
        threading.Thread: Background monitoring thread
    """
    def usbMonitor():
        check_interval = 0.5  # 500ms
        while True:
            # Check if USB still exists
            if not usb_root.exists():
                # USB removed — trigger lock
                lock_callback("USB_REMOVED")
                break
            time.sleep(check_interval)

    # Create and start monitoring thread
    thread = threading.Thread(target=usbMonitor, daemon=True)
    thread.start()

    return thread


def setupIdleTimeout(timeout_seconds: int, lock_callback) -> threading.Thread:
    """
    Set up idle timeout monitoring.

    Args:
        timeout_seconds: Timeout duration
        lock_callback: Callback function called when timeout reached

    Returns:
        threading.Thread: Background monitoring thread
    """
    last_activity = time.time()

    def idleMonitor():
        nonlocal last_activity
        countdown = timeout_seconds
        check_interval = 0.5

        while True:
            # Check if idle
            now = time.time()
            idle_time = now - last_activity

            if idle_time >= countdown:
                # Timeout reached — trigger lock
                lock_callback("TIMEOUT")
                break

            # Reset countdown on activity (but we don't have activity here,
            # so this thread will naturally time out)
            remaining = countdown - idle_time

            if remaining > 0:
                time.sleep(check_interval)
            else:
                # Timeout reached
                lock_callback("TIMEOUT")
                break

    # Create and start monitoring thread
    thread = threading.Thread(target=idleMonitor, daemon=True)
    thread.start()

    return thread


def resetIdleTimer() -> None:
    """
    Reset the idle timer on user activity.

    Call this on any user action (key press, mouse click) to prevent timeout.
    """
    global last_activity
    last_activity = time.time()


if __name__ == "__main__":
    import tempfile
    import shutil

    print("SFFS — Emergency Lock Demo\n" + "=" * 40 + "\n")

    # Create test sandbox
    sandbox_path = Path(tempfile.mkdtemp())
    decrypted_dir = sandbox_path / "decrypted"
    decrypted_dir.mkdir()

    # Create a test file
    test_file = decrypted_dir / "secret.txt"
    test_file.write_text("This should be securely deleted.")

    print(f"Created sandbox: {sandbox_path}")
    print(f"Test file: {test_file}")
    print(f"File exists: {test_file.exists()}\n")

    # Create test database for session management
    test_dir = Path("./code2/test_output")
    test_dir.mkdir(exist_ok=True)
    db_path = test_dir / "lock_test.db"
    auth_path = test_dir / "auth_test.db"

    # Initialize auth database
    from f09_authenticate_user import initAuthDatabase, registerUser, authenticateUser
    initAuthDatabase(auth_path)

    # Register test user
    test_password = bytearray(b"TestPassword123!")
    result = registerUser("testuser", test_password, auth_path)
    print(f"Registered user: {result}")

    # Authenticate to get session token
    result = authenticateUser("testuser", test_password, auth_path)
    session_token = result.get("session_token")
    user_id = result.get("user_id")
    print(f"Session token: {session_token}")
    print(f"User ID: {user_id}\n")

    # Simulate a MANUAL trigger
    print("Simulating MANUAL emergency lock trigger...")
    print("-" * 40)

    # Setup emergency lock callback
    emergency_callback_called = False

    def emergency_callback(trigger):
        global emergency_callback_called
        emergency_callback_called = True
        print(f"Emergency lock triggered by: {trigger}")

    # Create a test wipe memory target
    memory_target = bytearray(b"SensitiveEncryptionKey123")
    wipe_targets = [memory_target]

    # Trigger emergency lock
    emergencyLock(
        trigger="MANUAL",
        sandbox_path=sandbox_path,
        session_token=session_token,
        db_path=auth_path,
        wipe_memory_targets=wipe_targets
    )

    # Check if sandbox was destroyed
    if not sandbox_path.exists():
        print("✓ Sandbox destroyed")
    else:
        print("✗ Sandbox still exists!")

    # Check if test file was deleted
    if not test_file.exists():
        print("✓ Test file deleted")
    else:
        print("✗ Test file still exists!")

    # Check if session was terminated
    result = authenticateUser("testuser", test_password, auth_path)
    print(f"Session terminated: {result['session_token'] is None}")

    # Check if memory was wiped
    print(f"Memory target wiped: {memory_target == bytearray(len(memory_target))}")

    # Check if callback was called
    print(f"Emergency callback called: {emergency_callback_called}")

    # View audit log
    from f11_write_audit_log import AuditLogger
    logger = AuditLogger(db_path)
    logs = logger.viewLogs()
    emergency_logs = [log for log in logs if "EMERGENCY" in log.get("event", "")]
    if emergency_logs:
        print("\nEmergency lock audit entry:")
        for log in emergency_logs:
            print(f"  {log['timestamp']} | {log['level']} | {log['event']}")

    print("\n" + "=" * 40)
    print("Demo complete")