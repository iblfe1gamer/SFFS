"""
f17_config_loader.py — SFFS Student 3: Encrypted configuration

User preferences and feature flags can reveal operational details (cloud enabled,
paths, timeouts). Storing JSON encrypted at rest keeps casual USB loss from
exposing that metadata. JSON (not SQLite) keeps the decrypted shape easy to
inspect during development.

WHY optional encryption key:
- Development and CI can use plain JSON with an explicit warning; production
  should pass a 32-byte AES key derived post-authentication.
"""

from __future__ import annotations

import base64
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

# Why: AES-GCM authenticated encryption for config file at rest
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

DEFAULT_CONFIG: dict[str, Any] = {
    "version": "1.0",
    "theme": "dark",
    "auto_lock_timeout_seconds": 300,
    "max_login_attempts": 5,
    "cloud_sync_enabled": False,
    "cloud_sync_provider": "google_drive",
    "google_oauth_token_path": None,
    "default_encrypt_dir": None,
    "default_decrypt_dir": None,
    "log_max_entries": 10000,
    "hash_algorithm": "sha256",
    "key_size_bits": 2048,
    "pbkdf2_iterations": 310000,
    "ui_show_advanced": False,
    "last_updated": None,
}


def _merge_defaults(cfg: dict) -> dict:
    out = dict(DEFAULT_CONFIG)
    out.update(cfg)
    return out


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


def configLoader(
    action: str,
    config_dir: Path,
    updates: dict | None = None,
    encryption_key: bytes | None = None,
) -> dict:
    """
    Load, save, reset, or read a single config key.

    Args:
        action: ``load`` | ``save`` | ``reset`` | ``get``.
        config_dir: Directory containing ``sffs_config.enc`` (or ``.json`` plain).
        updates: For ``save``, partial dict to merge. For ``get``, ``{"key": "..."}``.
        encryption_key: 16/24/32-byte AES key; if None, plain JSON is used (dev only).

    Returns:
        Full config dict, or for ``get`` a dict ``{"key": ..., "value": ...}``.

    Raises:
        FileNotFoundError: On ``load``/``get`` when no config exists (after merge attempt).
        ValueError: Unknown action or invalid ``get`` payload.
    """
    config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    enc_path = config_dir / "sffs_config.enc"
    plain_path = config_dir / "sffs_config.json"

    def _read_current() -> dict:
        if encryption_key and enc_path.exists():
            raw = json.loads(enc_path.read_text(encoding="utf-8"))
            data = _decrypt_blob(raw, encryption_key)
            return json.loads(data.decode("utf-8"))
        if plain_path.exists():
            return json.loads(plain_path.read_text(encoding="utf-8"))
        return {}

    def _write(cfg: dict) -> None:
        cfg = _merge_defaults(cfg)
        cfg["last_updated"] = datetime.now().isoformat()
        blob = json.dumps(cfg, indent=2).encode("utf-8")
        if encryption_key is None:
            warnings.warn(
                "SFFS config written as PLAIN JSON (no encryption_key). "
                "Do not use in production.",
                UserWarning,
                stacklevel=3,
            )
            plain_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        else:
            wrapped = _encrypt_blob(blob, encryption_key)
            enc_path.write_text(json.dumps(wrapped, indent=2), encoding="utf-8")
            if plain_path.exists():
                plain_path.unlink()

    if action == "reset":
        cfg = dict(DEFAULT_CONFIG)
        _write(cfg)
        return _merge_defaults(cfg)

    if action == "load":
        base = _read_current()
        return _merge_defaults(base)

    if action == "save":
        current = _read_current()
        merged = _merge_defaults(current)
        if updates:
            merged.update(updates)
        _write(merged)
        return _merge_defaults(merged)

    if action == "get":
        if not updates or "key" not in updates:
            raise ValueError('get requires updates={"key": "<name>"}')
        full = configLoader("load", config_dir, encryption_key=encryption_key)
        k = updates["key"]
        return {"key": k, "value": full.get(k)}

    raise ValueError(f"Unknown action: {action}")


def validateConfig(config: dict) -> dict:
    """
    Validate config types and sensible ranges.

    Returns:
        ``{"valid": bool, "errors": list[str]}``
    """
    errors: list[str] = []
    if not isinstance(config.get("version"), str):
        errors.append("version must be str")
    if config.get("theme") not in ("dark", "light"):
        errors.append("theme must be dark|light")
    t = config.get("auto_lock_timeout_seconds")
    if not isinstance(t, int) or t < 30:
        errors.append("auto_lock_timeout_seconds must be int >= 30")
    if not isinstance(config.get("max_login_attempts"), int):
        errors.append("max_login_attempts must be int")
    ha = config.get("hash_algorithm")
    if ha not in ("sha256", "sha512", "blake2b"):
        errors.append("hash_algorithm invalid")
    return {"valid": len(errors) == 0, "errors": errors}


if __name__ == "__main__":
    test_root = Path(__file__).resolve().parent / "test_output"
    test_root.mkdir(parents=True, exist_ok=True)
    key = get_random_bytes(32)
    cfg_dir = test_root / "config_demo"
    cfg_dir.mkdir(exist_ok=True)
    c1 = configLoader("save", cfg_dir, {"theme": "light"}, encryption_key=key)
    c2 = configLoader("load", cfg_dir, encryption_key=key)
    assert c2["theme"] == "light"
    c3 = configLoader("save", cfg_dir, {"theme": "dark"}, encryption_key=key)
    print("Round-trip OK:", c3["theme"], validateConfig(c3))
