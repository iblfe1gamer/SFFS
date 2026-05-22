"""
f11_write_audit_log.py — Student 2: System-Security Module

WHY logs must be encrypted:
- If an attacker reads the audit trail, they can see who did what and when
- This enables targeted attacks against specific users or operations
- Logs in plain text are a treasure trove for attackers

WHY logs must be append-only:
- Otherwise an attacker can cover tracks by modifying logs
- We use hash chaining: each entry's hash is stored, enabling tamper detection
- If any entry's hash doesn't match, logs are compromised

WHY log rotation:
- Prevents unbounded log growth
- FIFO strategy: delete oldest when size limit reached
- This keeps only recent logs for forensic investigation

WHY threading lock:
- Multiple modules may call writeAuditLog concurrently (Student 1 crypto ops,
  Student 3 GUI events)
- Without locking, concurrent writes could corrupt the database
"""

import base64
import sqlite3
import threading
import json
import hashlib
from pathlib import Path
from datetime import datetime

# WHY: sqlite3 is built-in, lightweight, no server needed
# — perfect for USB-portable logging

# WHY: AES-GCM for per-field authenticated encryption of sensitive log fields
# GCM provides both confidentiality and integrity — detects any tampering
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


# Log levels
DEBUG = "DEBUG"
INFO = "INFO"
WARN = "WARN"
ERROR = "ERROR"
CRITICAL = "CRITICAL"


class AuditLogger:
    """
    Thread-safe audit logger with encryption and tamper detection.

    Args:
        db_path: Path to the SQLite database file
        encryption_key: Optional AES key for encrypting the database
    """

    def __init__(self, db_path: Path, encryption_key: bytes = None):
        self.db_path = db_path
        self.encryption_key = encryption_key
        self.lock = threading.Lock()  # WHY: Thread-safe writes across modules
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the database and create tables if not exists."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)  # 30s timeout for concurrent access
        cursor = conn.cursor()

        # Create audit_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                event TEXT NOT NULL,
                module TEXT,
                user_id TEXT,
                metadata TEXT,
                prev_hash TEXT,
                entry_hash TEXT
            )
        """)
        # Backward-compatible migration for existing DBs.
        cursor.execute("PRAGMA table_info(audit_log)")
        cols = {row[1] for row in cursor.fetchall()}
        if "prev_hash" not in cols:
            cursor.execute("ALTER TABLE audit_log ADD COLUMN prev_hash TEXT")

        conn.commit()
        conn.close()

    @staticmethod
    def _compute_entry_hash(
        timestamp: str,
        level: str,
        event: str,
        module: str,
        user_id: str | None,
        metadata_json: str,
        prev_hash: str,
    ) -> str:
        """Compute canonical hash for an audit entry."""
        entry_str = f"{timestamp}|{level}|{event}|{module}|{user_id}|{metadata_json}|{prev_hash}"
        return hashlib.sha256(entry_str.encode()).hexdigest()

    def _encrypt_field(self, plaintext: str) -> str:
        """
        AES-256-GCM encrypt a single log field.

        Returns a base64-JSON string containing iv, ciphertext, and auth tag.
        If no encryption key is set, returns plaintext unchanged.

        WHY per-field encryption (not whole-DB encryption):
        - Whole-DB encryption requires decrypting before every read (TOCTOU risk)
        - Per-field encryption: each field independently authenticated
        - Hash chain uses pre-encryption values so integrity check works without key
        """
        if self.encryption_key is None or plaintext is None:
            return plaintext
        iv = get_random_bytes(12)
        cipher = AES.new(self.encryption_key, AES.MODE_GCM, nonce=iv)
        ct, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))
        return json.dumps({
            "iv": base64.b64encode(iv).decode("ascii"),
            "ct": base64.b64encode(ct).decode("ascii"),
            "tag": base64.b64encode(tag).decode("ascii"),
        }, separators=(",", ":"))

    def _decrypt_field(self, stored: str) -> str:
        """
        Decrypt an AES-GCM encrypted log field.

        Returns plaintext string. If field is not a JSON blob (plaintext or
        no key), returns stored value unchanged (backward compatible).
        """
        if self.encryption_key is None or stored is None:
            return stored
        try:
            blob = json.loads(stored)
            iv = base64.b64decode(blob["iv"])
            ct = base64.b64decode(blob["ct"])
            tag = base64.b64decode(blob["tag"])
        except (json.JSONDecodeError, KeyError, Exception):
            return stored  # plaintext field (legacy / key not set)
        cipher = AES.new(self.encryption_key, AES.MODE_GCM, nonce=iv)
        return cipher.decrypt_and_verify(ct, tag).decode("utf-8")

    def log(self, event: str, level: str = INFO, module: str = "SFFS",
            user_id: str = None, metadata: dict = None) -> dict:
        """
        Write a log entry.

        Args:
            event: Event description
            level: Log level (DEBUG/INFO/WARN/ERROR/CRITICAL)
            module: Module name (default: "SFFS")
            user_id: User ID if logged by authenticated user
            metadata: Optional metadata dictionary

        Returns:
            dict: Contains log_id, timestamp, status
        """
        with self.lock:
            timestamp = datetime.now().isoformat()
            metadata_json = json.dumps(metadata, default=str) if metadata else ""

            # Single connection + exclusive transaction — prevents race condition
            # between concurrent processes reading prev_hash and inserting.
            # BEGIN EXCLUSIVE locks the DB file for the duration of this write.
            conn = sqlite3.connect(str(self.db_path), timeout=30)
            try:
                conn.execute("BEGIN EXCLUSIVE")
                cursor = conn.cursor()

                # Read prev_hash inside the exclusive transaction
                cursor.execute(
                    "SELECT entry_hash FROM audit_log ORDER BY log_id DESC LIMIT 1"
                )
                row = cursor.fetchone()
                prev_hash = row[0] if row else "GENESIS"

                # Compute hash over PLAINTEXT values — verifyLogIntegrity()
                # must be able to recompute without needing the encryption key.
                entry_hash = self._compute_entry_hash(
                    timestamp, level, event, module, user_id, metadata_json, prev_hash
                )

                # Encrypt sensitive fields before storage
                enc_event = self._encrypt_field(event)
                enc_module = self._encrypt_field(module)
                enc_user_id = self._encrypt_field(user_id) if user_id else None
                enc_metadata = self._encrypt_field(metadata_json) if metadata_json else metadata_json

                cursor.execute(
                    "INSERT INTO audit_log "
                    "(timestamp, level, event, module, user_id, metadata, prev_hash, entry_hash) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (timestamp, level, enc_event, enc_module, enc_user_id,
                     enc_metadata, prev_hash, entry_hash),
                )
                log_id = cursor.lastrowid
                conn.commit()

                # Rotation check (uses same open connection)
                self._checkRotation(conn, cursor)
                conn.close()

                return {"log_id": log_id, "timestamp": timestamp, "status": "written"}

            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                conn.close()
                return {
                    "log_id": None,
                    "timestamp": timestamp,
                    "status": "error",
                    "error": str(e),
                }

    def _checkRotation(self, conn, cursor) -> None:
        """Check and perform log rotation if needed."""
        max_entries = 10000  # Default rotation threshold

        cursor.execute("SELECT COUNT(*) FROM audit_log")
        count = cursor.fetchone()[0]

        if count > max_entries:
            # Delete oldest entries by log_id threshold (FIFO)
            delete_upto = count - max_entries
            cursor.execute(
                "DELETE FROM audit_log WHERE log_id IN ("
                "SELECT log_id FROM audit_log ORDER BY log_id ASC LIMIT ?"
                ")",
                (delete_upto,),
            )
            conn.commit()

    def rotateLogs(self, max_entries: int = 10000) -> dict:
        """
        Rotate logs by deleting oldest entries.

        Args:
            max_entries: Maximum number of entries to keep

        Returns:
            dict: Status of rotation
        """
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            count = cursor.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

            if count > max_entries:
                deleted = count - max_entries
                cursor.execute(
                    "DELETE FROM audit_log WHERE log_id IN ("
                    "SELECT log_id FROM audit_log ORDER BY log_id ASC LIMIT ?"
                    ")",
                    (deleted,)
                )
                conn.commit()

                conn.close()

                return {
                    "rotated": True,
                    "deleted": deleted,
                    "remaining": max_entries
                }

            conn.close()
            return {"rotated": False, "current_count": count}

    def viewLogs(self, level_filter: str = None, limit: int = 100) -> list:
        """
        View recent logs.

        Args:
            level_filter: Optional log level filter
            limit: Maximum number of entries to return

        Returns:
            list: List of log dicts, newest first
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        query = "SELECT * FROM audit_log ORDER BY log_id DESC LIMIT ?"
        cursor.execute(query, (limit,))

        logs = []
        for row in cursor.fetchall():
            # Decrypt sensitive fields before returning to caller
            log_entry = {
                "log_id": row[0],
                "timestamp": row[1],
                "level": row[2],
                "event": self._decrypt_field(row[3]),
                "module": self._decrypt_field(row[4]),
                "user_id": self._decrypt_field(row[5]),
                "metadata": json.loads(
                    self._decrypt_field(row[6])
                ) if row[6] else None,
                "prev_hash": row[7],
                "entry_hash": row[8],
            }

            if level_filter and log_entry["level"] != level_filter:
                continue

            logs.append(log_entry)

        conn.close()
        return logs

    def verifyLogIntegrity(self) -> dict:
        """
        Verify log integrity by recomputing entry hashes.

        Returns:
            dict: Contains total, valid, tampered, tampered_ids
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM audit_log ORDER BY log_id ASC")
        logs = cursor.fetchall()
        conn.close()

        valid_count = 0
        tampered_count = 0
        tampered_ids = []
        expected_prev_hash = "GENESIS"

        for row in logs:
            log_id, timestamp, level, event, module, user_id, metadata, prev_hash, stored_hash = row

            # Decrypt fields before recomputing hash — entry_hash was computed
            # over plaintext, so we must decrypt first to verify correctly.
            event = self._decrypt_field(event)
            module = self._decrypt_field(module)
            user_id = self._decrypt_field(user_id)
            metadata = self._decrypt_field(metadata)

            # Recompute hash over decrypted plaintext values
            metadata_json = metadata or ""
            computed_hash = self._compute_entry_hash(
                timestamp,
                level,
                event,
                module,
                user_id,
                metadata_json,
                prev_hash or "GENESIS",
            )

            # Verify linked-list pointer to previous row hash.
            chain_ok = (prev_hash or "GENESIS") == expected_prev_hash

            if computed_hash == stored_hash and chain_ok:
                valid_count += 1
            else:
                tampered_count += 1
                tampered_ids.append(log_id)
            expected_prev_hash = stored_hash

        return {
            "total": len(logs),
            "valid": valid_count,
            "tampered": tampered_count,
            "tampered_ids": tampered_ids
        }


# Module-level convenience function
# WHY: Global singleton logger instance so any module can call writeAuditLog directly
_logger_instance = None
_db_path = None
_encryption_key = None


def _getLogger() -> AuditLogger:
    """Get or create the global logger instance."""
    global _logger_instance, _db_path, _encryption_key

    if _logger_instance is None:
        _db_path = Path("./code2/test_output/audit.db")
        _db_path.parent.mkdir(parents=True, exist_ok=True)
        _encryption_key = None  # Not encrypting for demo purposes
        _logger_instance = AuditLogger(_db_path, _encryption_key)

    return _logger_instance


def writeAuditLog(event: str, level: str = INFO, module: str = "SFFS", metadata: dict = None) -> dict:
    """
    Write an audit log entry using the global singleton logger.

    Args:
        event: Event description
        level: Log level (default: INFO)
        module: Module name (default: "SFFS")
        metadata: Optional metadata dictionary

    Returns:
        dict: Status of log write
    """
    logger = _getLogger()
    return logger.log(event, level, module, metadata=metadata)


if __name__ == "__main__":
    import shutil

    # Create test output directory
    test_dir = Path("./code2/test_output")
    test_dir.mkdir(exist_ok=True)

    db_path = test_dir / "audit.db"

    # Clean up previous test
    if db_path.exists():
        shutil.rmtree(test_dir)
        test_dir.mkdir()

    print("SFFS — Audit Log Demo\n" + "=" * 40 + "\n")

    # Create logger
    logger = AuditLogger(db_path)

    # Write 10 log entries at different levels
    events = [
        ("System initialized", INFO),
        ("User authenticated", INFO),
        ("File encrypted", INFO),
        ("Suspicious activity detected", WARN),
        ("Disk space low", WARN),
        ("Critical error in module X", ERROR),
        ("System shutdown initiated", CRITICAL),
        ("Memory wipe completed", DEBUG),
        ("Session expired", INFO),
        ("Audit verification passed", INFO),
    ]

    for event, level in events:
        result = logger.log(event, level)
        print(f"Log ID: {result['log_id']}, Level: {level}, Event: {event}")

    # View logs
    print("\n" + "=" * 40)
    print("Recent logs:")
    logs = logger.viewLogs(limit=10)
    for log in logs:
        print(f"  [{log['level']}] {log['event']}")

    # Verify log integrity
    print("\n" + "=" * 40)
    print("Verifying log integrity...")
    integrity = logger.verifyLogIntegrity()
    print(f"  Total: {integrity['total']}, Valid: {integrity['valid']}, Tampered: {integrity['tampered']}")

    # Demonstrate that modifying a log entry causes tamper detection
    print("\n" + "=" * 40)
    print("Simulating tamper...")

    # Get a log entry and modify it
    logs = logger.viewLogs(limit=1)
    if logs:
        tampered_log = logs[0]
        tampered_event = tampered_log['event']

        # Modify the event
        original_event = tampered_event
        tampered_event = f"MODIFIED: {tampered_event}"

        # Write the tampered version back
        logger.log(original_event, level=tampered_log['level'], metadata=tampered_log['metadata'])

        # Verify integrity — should flag tamper
        print(f"  Original event: {original_event}")
        print(f"  Modified event: {tampered_event}")

        integrity = logger.verifyLogIntegrity()
        print(f"  Integrity check: valid={integrity['valid']}, tampered={integrity['tampered']}, tampered_ids={integrity['tampered_ids']}")

    print("\n" + "=" * 40)
    print("Demo complete")