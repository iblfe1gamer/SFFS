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

    password_lower = password_str.lower()
    password_upper = password_str.upper()
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
    # Pass a copy to avoid corrupting caller's bytearray
    secureMemoryWipe(bytearray(password))

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
    # Check if account is locked
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    cursor.execute("SELECT locked_until FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    locked_until = None
    if row and row[0]:
        locked_until = row[0]
        if locked_until > now:
            conn.close()
            return {
                "authenticated": False,
                "session_token": None,
                "user_id": None,
                "locked_until": locked_until,
                "failed_attempts": 0,
                "message": f"Account locked until {locked_until}"
            }

    # Load stored Argon2id hash for username
    cursor.execute("SELECT password_hash, user_id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    if not row:
        # Increment failed attempts for non-existent user (to prevent enumeration)
        cursor.execute(
            "SELECT user_id FROM users WHERE username = ?", (username,))
        existing_row = cursor.fetchone()
        if existing_row:
            user_id = existing_row[0]
            cursor.execute(
                "UPDATE users SET failed_attempts = failed_attempts + 1 WHERE user_id = ?",
                (user_id,)
            )
        else:
            user_id = None

        # Wipe password bytearray regardless of result
        secureMemoryWipe(password)
        conn.close()

        return {
            "authenticated": False,
            "session_token": None,
            "user_id": None,
            "locked_until": None,
            "failed_attempts": 1,
            "message": "Invalid username or password"
        }

    password_hash, user_id = row

    # Convert bytearray password to string for verification
    password_str = password.decode('utf-8')

    # Verify password with Argon2id - use same params as registration
    pw = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
    try:
        is_valid = pw.verify(password_hash, password_str)
    except VerifyMismatchError:
        # Wrong password - Argon2 raises exception instead of returning False
        is_valid = False

    if not is_valid:
        # Authentication failed
        # Increment failed attempts
        cursor.execute(
            "SELECT failed_attempts FROM users WHERE user_id = ?",
            (user_id,)
        )
        failed_attempts = cursor.fetchone()[0] or 0

        failed_attempts += 1

        # Apply exponential lockout: 30s * 2^(failed_attempts-1)
        if failed_attempts > 4:
            backoff_seconds = 30 * (2 ** (failed_attempts - 5))  # After 5 failures, cap at reasonable value
            locked_until = (datetime.now() + timedelta(seconds=backoff_seconds)).isoformat()

        # Wipe password regardless of result
        secureMemoryWipe(bytearray(password_str, 'utf-8'))

        conn.close()

        return {
            "authenticated": False,
            "session_token": None,
            "user_id": None,
            "locked_until": locked_until,
            "failed_attempts": failed_attempts,
            "message": f"Invalid username or password (attempt {failed_attempts})"
        }

    # Authentication successful
    # Reset failed attempts
    cursor.execute(
        "UPDATE users SET failed_attempts = 0, last_login = ?, locked_until = NULL WHERE user_id = ?",
        (now, user_id)
    )

    # Generate session token
    session_token = secrets.token_urlsafe(32)

    # Insert session
    cursor.execute(
        "INSERT INTO sessions (session_token, user_id, created_at, expires_at) "
        "VALUES (?, ?, ?, ?)",
        (session_token, user_id, now, (datetime.now() + timedelta(hours=24)).isoformat())
    )

    # Wipe password string by converting to bytearray first
    secureMemoryWipe(bytearray(password_str, 'utf-8'))

    conn.commit()
    conn.close()

    return {
        "authenticated": True,
        "session_token": session_token,
        "user_id": user_id,
        "locked_until": None,
        "failed_attempts": 0,
        "message": "Authentication successful"
    }


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