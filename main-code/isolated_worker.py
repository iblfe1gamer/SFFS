#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
isolated_worker.py - controller/worker split foundation for SFFS.

This worker runs sensitive decrypt operations in a separate Python process
boundary. It is a stepping stone toward OS-level containment. In this version,
it enforces strict path policy and performs decrypt+integrity verification.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import os
import hmac
import hashlib
import time
import threading
from pathlib import Path

# Ensure sibling student modules import cleanly when invoked directly
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "code1", _ROOT / "code2", _ROOT / "code3", _ROOT / "main-code"):
    s = str(_p)
    if s not in sys.path:
        sys.path.insert(0, s)

from f03_decrypt_file import SecurityError, decryptFile
from f05_verify_hash import verifyHash
from f06_secure_key_storage import unwrapAESKey

_SEEN_NONCES: dict[str, int] = {}
_NONCE_TTL_SECONDS = 30


def _purge_old_nonces(now: int) -> None:
    stale = [k for k, t in _SEEN_NONCES.items() if now - t > _NONCE_TTL_SECONDS]
    for k in stale:
        _SEEN_NONCES.pop(k, None)


def _require_within(child: Path, parent: Path) -> None:
    child_r = child.resolve()
    parent_r = parent.resolve()
    if parent_r != child_r and parent_r not in child_r.parents:
        raise PermissionError(f"Path policy violation: {child_r} is outside {parent_r}")


_SYSTEM_PATHS = [
    Path("C:\\Windows"),
    Path("C:\\Program Files"),
    Path("C:\\Program Files (x86)"),
    Path("C:\\ProgramData"),
    Path("/etc"),
    Path("/usr"),
    Path("/var"),
    Path("/boot"),
    Path("/sys"),
    Path("/proc"),
]


def _require_not_system_path(path: Path) -> None:
    p = path.resolve()
    for sp in _SYSTEM_PATHS:
        # Resolve each system path too so that Windows symlinks (e.g. a junction
        # pointing into C:\Windows from a user-writable directory) do not bypass
        # the check.  resolve() is a no-op for paths that don't exist.
        try:
            sp_r = sp.resolve()
        except OSError:
            sp_r = sp
        if sp_r.exists() and (p == sp_r or sp_r in p.parents):
            raise PermissionError(f"Output path denied: {path} overlaps with system path")


def _canonical_json(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _verify_envelope(envelope: dict) -> dict:
    """
    Verify signed IPC envelope and return trusted payload.
    """
    ipc_key = os.environ.get("SFFS_IPC_KEY", "")
    if not ipc_key:
        raise PermissionError("Missing IPC key")
    payload = envelope.get("payload")
    nonce = envelope.get("nonce")
    session_token = envelope.get("session_token")
    signature = envelope.get("signature")
    issued_at = envelope.get("issued_at", 0)
    if not isinstance(payload, dict):
        raise ValueError("Invalid payload")
    if not all(isinstance(v, str) for v in (nonce, session_token, signature)):
        raise ValueError("Invalid envelope metadata")

    # Reject stale envelopes quickly.
    now = int(time.time())
    if abs(now - int(issued_at)) > 30:
        raise PermissionError("Stale IPC envelope")
    _purge_old_nonces(now)
    if nonce in _SEEN_NONCES:
        raise PermissionError("Replay IPC envelope nonce")
    _SEEN_NONCES[nonce] = now

    msg = _canonical_json(
        {
            "payload": payload,
            "nonce": nonce,
            "session_token": session_token,
            "issued_at": int(issued_at),
        }
    )
    expected = hmac.new(ipc_key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PermissionError("Invalid IPC signature")
    return payload


def _load_policy() -> dict:
    policy_path = os.environ.get("SFFS_WORKER_POLICY")
    if not policy_path:
        raise PermissionError("Missing worker policy path")
    p = Path(policy_path)
    if not p.exists():
        raise FileNotFoundError(f"Worker policy not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _policy_guard(
    action: str,
    output_dir: Path,
    sandbox_root: Path | None,
    policy: dict,
    is_external_output: bool = False,
) -> None:
    allowed_actions = policy.get("allowed_actions", [])
    if action not in allowed_actions:
        raise PermissionError(f"Action '{action}' denied by policy")
    if is_external_output:
        _require_not_system_path(output_dir)
        return
    assert sandbox_root is not None
    allowed_rel = policy.get("output_root_relative", "decrypted")
    expected = (sandbox_root / allowed_rel).resolve()
    if output_dir.resolve() != expected:
        raise PermissionError("Output directory denied by policy")


def _action_decrypt(payload: dict, master_password: str) -> dict:
    sffs_path = Path(payload["sffs_path"]).resolve()
    keystore_path = Path(payload["keystore_path"]).resolve()
    output_dir = Path(payload["output_dir"]).resolve()
    is_external_output = payload.get("is_external_output", False)
    # master_password received via stdin, not payload (never in CLI args)
    wrapped = base64.b64decode(payload["wrap_data_b64"])

    if is_external_output:
        _require_not_system_path(output_dir)
    else:
        sandbox_root = Path(payload["sandbox_root"]).resolve()
        _require_within(output_dir, sandbox_root)
    for p in (sffs_path, keystore_path):
        if not p.exists():
            raise FileNotFoundError(str(p))

    aes_key = unwrapAESKey(
        wrapped,
        keystore_path,
        master_password,
        expected_sffs_path=sffs_path,
    )

    # Look up expected provenance token from payload (provided by SFFSCore from
    # the provenance table).  Empty string means V2 file or token not registered.
    expected_token_hex = payload.get("expected_token_hex", "")
    expected_token: bytes | None = None
    if expected_token_hex:
        try:
            expected_token = bytes.fromhex(expected_token_hex)
        except ValueError:
            expected_token = None

    dec = decryptFile(sffs_path, aes_key, output_dir, expected_token=expected_token)
    vr = verifyHash(dec["hash_pre"], dec["hash_post"])
    if not vr.get("match"):
        outp = Path(dec["output_path"])
        if outp.exists():
            outp.unlink()
        raise SecurityError(vr.get("message", "Integrity verification failed"))

    result: dict = {
        "output_path": str(Path(dec["output_path"]).resolve()),
        "hash_pre": dec["hash_pre"],
        "integrity": "verified",
        "status": "decrypted",
    }
    ft = dec.get("file_token")
    if ft:
        result["file_token_hex"] = ft.hex()
    return result


def _nonce_purge_loop() -> None:
    """Background thread: purge expired nonces every 10 s.

    WHY a background thread:
    Nonces are only purged when _verify_envelope() is called. Between calls, the
    _SEEN_NONCES dict grows unboundedly. An attacker can send a burst of requests
    (all with unique nonces), wait >30 s for those nonces to expire, then replay
    any of them — the replay check sees an empty dict and passes. Periodic
    background purging closes this window.
    """
    while True:
        time.sleep(10)
        _purge_old_nonces(int(time.time()))


def main() -> int:
    # Start background nonce purge before processing any request.
    threading.Thread(target=_nonce_purge_loop, daemon=True, name="nonce-purge").start()

    ap = argparse.ArgumentParser(description="SFFS isolated worker")
    ap.add_argument("--action", required=True, choices=("decrypt",))
    ap.add_argument("--payload", required=True, help="JSON payload string")
    args = ap.parse_args()

    # SECURITY: master_password is read from stdin, never from CLI args.
    # This prevents it appearing in process argument lists (tasklist /V,
    # /proc/<pid>/cmdline, audit logs, etc.).
    master_password = sys.stdin.readline().rstrip("\n")
    if not master_password:
        print(json.dumps({"ok": False, "error": "PermissionError: Missing master password on stdin"}))
        return 1

    try:
        envelope = json.loads(args.payload)
        payload = _verify_envelope(envelope)
        policy = _load_policy()
        if args.action == "decrypt":
            _is_external = payload.get("is_external_output", False)
            _sr = payload.get("sandbox_root", "")
            _policy_guard(
                action="decrypt",
                output_dir=Path(payload["output_dir"]),
                sandbox_root=Path(_sr) if _sr else None,
                policy=policy,
                is_external_output=_is_external,
            )
            out = _action_decrypt(payload, master_password)
        else:
            raise ValueError(f"Unsupported action: {args.action}")
        print(json.dumps({"ok": True, "result": out}))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
