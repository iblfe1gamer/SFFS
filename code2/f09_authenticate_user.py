"""
f09_authenticate_user.py — Student 2: System-Security Module

Argon2id is a memory-hard KDF (Key Derivation Function) that requires large amounts
of RAM to compute, making GPU attacks expensive. It won the Password Hashing
Competition (PHC) in 2015.

OWASP 2023 recommendations for Argon2 parameters:
- time_cost: 3 (iterations)
- memory_cost: 65536 (64 MB)
- parallelism: 4
- hash_len: 32 (bytes)

These parameters balance security (memory-hardness) with reasonable runtime.

WHY the plain-text password must be wiped immediately after hashing:
- The password exists in memory only during the hashing operation
- Even a millisecond of exposure allows memory dump extraction
- We must call secureMemoryWipe() immediately after hashing

Why hmac.compare_digest() is used for hash comparison:
- Timing attacks can detect password matches via response time differences
- compare_digest() uses constant-time comparison regardless of match position
- This prevents attackers from guessing passwords character-by-character

Lockout policy:
- On first failure: 30 seconds
- On second: 60 seconds
- On third: 120 seconds
- On fourth: 300 seconds (5 minutes)
- Exponential backoff: 2^N * 30 seconds
"""

from pathlib import Path
import sqlite3
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta
import secrets

# WHY Argon2id: winner of the Password Hashing Competition (PHC), memory-hard
# — resistant to GPU and ASIC brute-force attacks; preferred over PBKDF2 or bcrypt
try:
    from argon2 import PasswordHasher, Type
    from argon2.exceptions import VerifyMismatchError
    ARGON2_ID = Type.ID  # Use Argon2id (hybrid of Argon2i and Argon2d)
except ImportError:
    raise ImportError("Install argon2-cffi: pip install argon2-cffi")

# Import secureMemoryWipe from sibling module
from f08_secure_memory_wipe import secureMemoryWipe

# Pre-computed dummy hash for constant-time rejection of unknown usernames.
# Without this, unknown users return instantly while known users wait ~100ms
# for Argon2 verify — attacker can enumerate valid usernames via timing.
_DUMMY_HASH: str = PasswordHasher(
    time_cost=3, memory_cost=65536, parallelism=4
).hash("sffs_dummy_constant_xK9#mQ2_not_a_real_password")


def _compute_lock_until(failed_attempts: int) -> str | None:
    """Return lock-until timestamp for current failed attempts."""
    if failed_attempts < 1:
        return None
    # 30s, 60s, 120s, ... (cap at 1 hour to avoid pathological lockouts)
    backoff_seconds = min(30 * (2 ** (failed_attempts - 1)), 3600)
    return (datetime.now() + timedelta(seconds=backoff_seconds)).isoformat()


def initAuthDatabase(db_path: Path) -> None:
    """
    Initialize the authentication database with users and sessions tables.

    Args:
        db_path: Path to the SQLite database file
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT,
            last_login TEXT,
            failed_attempts INTEGER DEFAULT 0,
            locked_until TEXT
        )
    """)

    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            user_id TEXT,
            created_at TEXT,
            expires_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def registerUser(username: str, password: bytearray, db_path: Path) -> dict:
    """
    Register a new user with password hashing.

    Args:
        username: Username (must be unique)
        password: Plain-text password as bytearray
        db_path: Path to the authentication database

    Returns:
        dict: Contains user_id and status

    Raises:
        ValueError: If password policy is not met
    """
    # Validate password policy
    password_str = password.decode('utf-8')
    if len(password_str) < 12:
        raise ValueError("Password must be at least 12 characters")

    has_upper = any(c.isupper() for c in password_str)
    has_lower = any(c.islower() for c in password_str)
    has_digit = any(c.isdigit() for c in password_str)
    has_special = any(not c.isalnum() for c in password_str)

    if not (has_upper and has_lower and has_digit and has_special):
        raise ValueError(
            "Password must contain uppercase, lowercase, digit, and special character"
        )

    # Hash with Argon2id (use default hash_len for compatibility with verify)
    pw = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
    password_hash = pw.hash(password_str)

    # Wipe password bytearray immediately after hashing
    secureMemoryWipe(password)

    # Generate user_id
    user_id = str(uuid.uuid4())

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (user_id, username, password_hash, created_at, last_login) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, username, password_hash, datetime.now().isoformat(), None)
        )
        conn.commit()
        return {"user_id": user_id, "status": "registered"}
    except sqlite3.IntegrityError:
        conn.rollback()
        return {"user_id": None, "status": "error", "message": "Username already exists"}
    finally:
        conn.close()


def authenticateUser(username: str, password: bytearray, db_path: Path) -> dict:
    """
    Authenticate a user with password verification.

    Args:
        username: Username to authenticate
        password: Plain-text password as bytearray
        db_path: Path to the authentication database

    Returns:
        dict: Contains authenticated status, session_token, user_id, locked_until,
              failed_attempts, and message

    Security Notes:
        WHY we use bytearray for password:
        - It can be wiped immediately after use
        - Strings are immutable and interned
        - This prevents accidental memory exposure
    """
    pw = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    try:
        cursor.execute(
            "SELECT user_id, password_hash, failed_attempts, locked_until FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()

        # Unknown user: run dummy Argon2 verify to equalize response time.
        # Without this, unknown users return instantly (~0ms) vs known users
        # (~100ms for Argon2). Attacker can enumerate valid usernames via timing.
        if not row:
            try:
                pw.verify(_DUMMY_HASH, password.decode("utf-8", errors="replace"))
            except Exception:
                pass  # always fails — only here for timing equalization
            secureMemoryWipe(password)
            return {
                "authenticated": False,
                "session_token": None,
                "user_id": None,
                "locked_until": None,
                "failed_attempts": 0,
                "message": "Invalid username or password",
            }

        user_id, password_hash, failed_attempts, locked_until = row
        failed_attempts = int(failed_attempts or 0)

        # Enforce lockout window first.
        if locked_until and locked_until > now:
            secureMemoryWipe(password)
            return {
                "authenticated": False,
                "session_token": None,
                "user_id": None,
                "locked_until": locked_until,
                "failed_attempts": failed_attempts,
                "message": f"Account locked until {locked_until}",
            }

        password_str = password.decode("utf-8")
        try:
            is_valid = pw.verify(password_hash, password_str)
        except VerifyMismatchError:
            is_valid = False
        finally:
            # WHY finally: guarantees wipe even if pw.verify() raises an unexpected
            # exception (e.g. argon2.exceptions.VerificationError, MemoryError).
            # Without finally, any non-VerifyMismatchError propagates and skips wipe.
            secureMemoryWipe(password)

        if not is_valid:
            failed_attempts += 1
            new_locked_until = _compute_lock_until(failed_attempts)
            cursor.execute(
                "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE user_id = ?",
                (failed_attempts, new_locked_until, user_id),
            )
            conn.commit()
            return {
                "authenticated": False,
                "session_token": None,
                "user_id": None,
                "locked_until": new_locked_until,
                "failed_attempts": failed_attempts,
                "message": f"Invalid username or password (attempt {failed_attempts})",
            }

        # Success path: reset lockout state and create session.
        cursor.execute(
            "UPDATE users SET failed_attempts = 0, last_login = ?, locked_until = NULL WHERE user_id = ?",
            (now, user_id),
        )
        session_token = secrets.token_urlsafe(32)
        cursor.execute(
            "INSERT INTO sessions (session_token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (session_token, user_id, now, (datetime.now() + timedelta(hours=24)).isoformat()),
        )
        conn.commit()
        return {
            "authenticated": True,
            "session_token": session_token,
            "user_id": user_id,
            "locked_until": None,
            "failed_attempts": 0,
            "message": "Authentication successful",
        }
    finally:
        conn.close()


def validateSession(session_token: str, db_path: Path) -> bool:
    """
    Validate a session token.

    Args:
        session_token: Session token to validate
        db_path: Path to the authentication database

    Returns:
        bool: True if valid and not expired
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, expires_at FROM sessions WHERE session_token = ?", (session_token,))
    row = cursor.fetchone()

    conn.close()

    if not row:
        return False

    expires_at = row[1]
    now = datetime.now().isoformat()

    return expires_at > now


def terminateSession(session_token: str, db_path: Path) -> None:
    """
    Terminate a session by deleting it from the database.

    Args:
        session_token: Session token to terminate
        db_path: Path to the authentication database
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    import shutil
    import os

    # Create test database
    test_dir = Path("./test_output")
    test_dir.mkdir(exist_ok=True)
    db_path = test_dir / "auth_test.db"

    # Clean up previous test database
    if db_path.exists():
        shutil.rmtree(test_dir)
        test_dir.mkdir()

    print("SFFS — User Authentication Demo\n" + "=" * 40 + "\n")

    # Initialize database
    print("Initializing database...")
    initAuthDatabase(db_path)

    # Register user with test password
    test_password = bytearray(b"TestPassword123!")
    print(f"Registering user with password: {test_password!r}")

    result = registerUser("testuser", test_password, db_path)
    print(f"Result: {result}\n")

    # Authenticate successfully
    print("Attempting authentication...")
    result = authenticateUser("testuser", test_password, db_path)
    print(f"Result: {result}\n")

    # Attempt wrong password
    print("Attempting with wrong password...")
    result = authenticateUser("testuser", bytearray(b"WrongPassword123!"), db_path)
    print(f"Result: {result}\n")

    # Show lockout after 5 failures
    print("Testing lockout (will take time)...")
    for i in range(5):
        wrong_password = bytearray(b"WrongPassword123!")
        result = authenticateUser("testuser", wrong_password, db_path)
        print(f"  Attempt {i+1}: {result['message']} (locked_until: {result['locked_until']})")

    # Clean up test database
    if db_path.exists():
        shutil.rmtree(test_dir)
        print(f"\nCleaned up test database: {db_path}")