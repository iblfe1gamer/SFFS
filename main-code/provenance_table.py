"""
provenance_table.py — Per-file provenance registry for SFFS.

Each encrypted file gets a unique 32-byte token stored in its header
(SFFS V3 format).  This table persists the mapping:

    hash_pre (SHA-256 of original plaintext) → token_hex

so that decryption can verify the header token matches what was registered
at encrypt time before any decryption is attempted.

SECURITY — table encryption:
The table is stored encrypted (AES-256-GCM) using a key derived from the
user's master password.  An attacker with read access to sffs_data/ cannot
read the tokens without the password — even with both the table and an
.sffs file they cannot verify or forge provenance.
"""

from __future__ import annotations

import datetime
import hmac
import json
import os
from pathlib import Path


def _derive_table_key(master_password: str, salt: bytes) -> bytes:
    """Derive a 32-byte AES key from master_password + salt using Argon2id."""
    from argon2.low_level import Type, hash_secret_raw
    return hash_secret_raw(
        secret=master_password.encode("utf-8"),
        salt=salt,
        time_cost=2,
        memory_cost=32768,
        parallelism=2,
        hash_len=32,
        type=Type.ID,
    )


class ProvenanceTable:
    """
    Encrypted persistent mapping of file content hashes to per-file provenance tokens.

    The on-disk file is AES-256-GCM encrypted so the token values cannot be
    read without the master password.  Format:

        salt(16) | iv(12) | ciphertext | auth_tag(16)

    where ciphertext = AES-GCM(json_bytes, key=derive(password, salt)).

    Thread-safety: not thread-safe; callers must coordinate if concurrent
    encrypt/decrypt is possible (SFFSCore serializes these via session lock).
    """

    _SALT_LEN = 16
    _IV_LEN = 12

    def __init__(self, table_path: Path, master_password: str) -> None:
        self._path = table_path
        self._password = master_password
        self._data: dict[str, dict] = {}
        self._salt: bytes = os.urandom(self._SALT_LEN)  # regenerated only on first save
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = self._path.read_bytes()
            # Layout: salt(16) | iv(12) | aesgcm_ciphertext_with_tag
            if len(raw) < self._SALT_LEN + self._IV_LEN + 16:
                return  # too short — treat as empty
            salt = raw[:self._SALT_LEN]
            iv   = raw[self._SALT_LEN : self._SALT_LEN + self._IV_LEN]
            blob = raw[self._SALT_LEN + self._IV_LEN :]
            key = _derive_table_key(self._password, salt)
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            plaintext = AESGCM(key).decrypt(iv, blob, None)
            parsed = json.loads(plaintext.decode("utf-8"))
            if isinstance(parsed, dict):
                self._data = parsed
                self._salt = salt  # reuse same salt for subsequent saves
        except Exception:
            # Wrong password, corrupted file, or first run — start empty
            self._data = {}

    def _save(self) -> None:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        self._path.parent.mkdir(parents=True, exist_ok=True)
        plaintext = json.dumps(self._data, indent=2).encode("utf-8")
        key = _derive_table_key(self._password, self._salt)
        iv = os.urandom(self._IV_LEN)
        ciphertext = AESGCM(key).encrypt(iv, plaintext, None)
        self._path.write_bytes(self._salt + iv + ciphertext)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, hash_pre: str, token: bytes, sffs_path: Path) -> None:
        """
        Register a new file token.

        Args:
            hash_pre:  SHA-256 hex digest of the original plaintext.
            token:     32-byte provenance token embedded in ciphertext.
            sffs_path: Path to the .sffs file (for audit trail only).
        """
        self._data[hash_pre] = {
            "token_hex": token.hex(),
            "sffs_path": str(sffs_path),
            "registered_at": datetime.datetime.now().isoformat(),
        }
        self._save()

    def lookup(self, hash_pre: str) -> bytes | None:
        """
        Return the token for a given hash_pre, or None if not registered.
        """
        entry = self._data.get(hash_pre)
        if entry is None:
            return None
        try:
            return bytes.fromhex(entry["token_hex"])
        except (KeyError, ValueError):
            return None

    def verify(self, hash_pre: str, token: bytes) -> bool:
        """
        Constant-time check: does the stored token match the given token?
        Returns False if hash_pre is not registered.
        """
        expected = self.lookup(hash_pre)
        if expected is None or len(expected) != len(token):
            return False
        return hmac.compare_digest(expected, token)

    def remove(self, hash_pre: str) -> bool:
        """Remove entry for hash_pre.  Returns True if it existed."""
        if hash_pre in self._data:
            del self._data[hash_pre]
            self._save()
            return True
        return False

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, hash_pre: str) -> bool:
        return hash_pre in self._data
