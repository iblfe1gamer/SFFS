"""
wrap_store.py — Encrypted SQLite store for RSA-wrapped AES keys.

Replaces per-file .aeswrap/.wrapref sidecar files with a single
AES-GCM encrypted SQLite database. Encryption pattern matches
f17_config_loader.py: _encrypt_blob / _decrypt_blob over AES-GCM.

Lifecycle per DB operation:
  1. Decrypt wrap_store.enc -> temp SQLite file
  2. Execute operation
  3. Re-encrypt and overwrite wrap_store.enc
"""

from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def _encrypt_blob(plaintext: bytes, key: bytes) -> dict:
    iv = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ct, tag = cipher.encrypt_and_digest(plaintext)
    return {
        "iv": base64.b64encode(iv).decode("ascii"),
        "ciphertext": base64.b64encode(ct).decode("ascii"),
        "tag": base64.b64encode(tag).decode("ascii"),
    }


def _decrypt_blob(wrapper: dict, key: bytes) -> bytes:
    iv = base64.b64decode(wrapper["iv"])
    ct = base64.b64decode(wrapper["ciphertext"])
    tag = base64.b64decode(wrapper["tag"])
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    return cipher.decrypt_and_verify(ct, tag)


def _sha256_file(path: Path) -> str:
    """Stream file in 8 MB chunks — safe for multi-GB .sffs files."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class _DbContext:
    """Decrypt .enc -> temp SQLite -> operate -> re-encrypt on exit."""

    def __init__(self, enc_path: Path, key: bytes, tmp_dir: Optional[Path] = None) -> None:
        self._enc_path = enc_path
        self._key = key
        self._tmp_dir = tmp_dir
        self._tmp_path: Optional[Path] = None
        self._conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        tmp_kw = {"dir": str(self._tmp_dir)} if self._tmp_dir else {}
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False, **tmp_kw)
        self._tmp_path = Path(tmp.name)
        tmp.close()
        try:
            if self._enc_path.exists():
                wrapper = json.loads(self._enc_path.read_text(encoding="utf-8"))
                raw_db = _decrypt_blob(wrapper, self._key)
                self._tmp_path.write_bytes(raw_db)
            self._conn = sqlite3.connect(str(self._tmp_path))
        except Exception:
            if self._tmp_path and self._tmp_path.exists():
                self._tmp_path.unlink(missing_ok=True)
            raise
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if self._conn:
                self._conn.commit()
                self._conn.close()
            if self._tmp_path and self._tmp_path.exists():
                raw_db = self._tmp_path.read_bytes()
                wrapped = _encrypt_blob(raw_db, self._key)
                self._enc_path.write_text(json.dumps(wrapped, indent=2), encoding="utf-8")
        finally:
            if self._tmp_path and self._tmp_path.exists():
                self._tmp_path.unlink(missing_ok=True)
        return False


class WrapStore:
    """Encrypted SQLite store for RSA-wrapped AES keys."""

    def __init__(self, db_path: Path, encryption_key: bytes, tmp_dir: Optional[Path] = None) -> None:
        self._enc_path = db_path.with_suffix(".enc")
        self.encryption_key = encryption_key
        self._tmp_dir = tmp_dir

    def _ctx(self) -> _DbContext:
        return _DbContext(self._enc_path, self.encryption_key, self._tmp_dir)

    def initialize(self) -> None:
        """Create wrap_store table if not exists."""
        with self._ctx() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS wrap_store (
                    sffs_sha256  TEXT PRIMARY KEY,
                    wrap_data    BLOB NOT NULL,
                    sffs_filename TEXT NOT NULL,
                    created_at   TEXT NOT NULL,
                    user_id      TEXT
                )
                """
            )

    def store(self, sffs_path: Path, wrap_data: bytes, user_id: Optional[str]) -> None:
        """Store wrapped AES key keyed by SHA-256 of the .sffs file content."""
        sha = _sha256_file(sffs_path)
        ts = datetime.now(timezone.utc).isoformat()
        with self._ctx() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO wrap_store "
                "(sffs_sha256, wrap_data, sffs_filename, created_at, user_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (sha, wrap_data, sffs_path.name, ts, user_id),
            )

    def lookup(self, sffs_path: Path) -> bytes:
        """Return wrap_data bytes for the given .sffs file."""
        sha = _sha256_file(sffs_path)
        with self._ctx() as conn:
            row = conn.execute(
                "SELECT wrap_data FROM wrap_store WHERE sffs_sha256 = ?", (sha,)
            ).fetchone()
        if row is None:
            raise FileNotFoundError(f"No wrap entry for: {sffs_path.name}")
        return bytes(row[0])

    def delete(self, sffs_path: Path) -> None:
        """Remove wrap entry for the given .sffs file."""
        sha = _sha256_file(sffs_path)
        with self._ctx() as conn:
            conn.execute(
                "DELETE FROM wrap_store WHERE sffs_sha256 = ?", (sha,)
            )
