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
import json
import sys
import os
import hmac
import hashlib
import time
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


def _require_within(child: Path, parent: Path) -> None:
    child_r = child.resolve()
    parent_r = parent.resolve()
    if parent_r != child_r and parent_r not in child_r.parents:
        raise PermissionError(f"Path policy violation: {child_r} is outside {parent_r}")


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


def _policy_guard(action: str, output_dir: Path, sandbox_root: Path, policy: dict) -> None:
    allowed_actions = policy.get("allowed_actions", [])
    if action not in allowed_actions:
        raise PermissionError(f"Action '{action}' denied by policy")
    allowed_rel = policy.get("output_root_relative", "decrypted")
    expected = (sandbox_root / allowed_rel).resolve()
    if output_dir.resolve() != expected:
        raise PermissionError("Output directory denied by policy")


def _action_decrypt(payload: dict) -> dict:
    sffs_path = Path(payload["sffs_path"]).resolve()
    wrap_path = Path(payload["wrap_path"]).resolve()
    keystore_path = Path(payload["keystore_path"]).resolve()
    output_dir = Path(payload["output_dir"]).resolve()
    sandbox_root = Path(payload["sandbox_root"]).resolve()
    master_password = payload["master_password"]

    # Policy: output must remain under sandbox; input artifacts must exist.
    _require_within(output_dir, sandbox_root)
    for p in (sffs_path, wrap_path, keystore_path):
        if not p.exists():
            raise FileNotFoundError(str(p))

    wrapped = wrap_path.read_bytes()
    aes_key = unwrapAESKey(wrapped, keystore_path, master_password)
    dec = decryptFile(sffs_path, aes_key, output_dir)
    vr = verifyHash(dec["hash_pre"], dec["hash_post"])
    if not vr.get("match"):
        outp = Path(dec["output_path"])
        if outp.exists():
            outp.unlink()
        raise SecurityError(vr.get("message", "Integrity verification failed"))

    return {
        "output_path": str(Path(dec["output_path"]).resolve()),
        "integrity": "verified",
        "status": "decrypted",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="SFFS isolated worker")
    ap.add_argument("--action", required=True, choices=("decrypt",))
    ap.add_argument("--payload", required=True, help="JSON payload string")
    args = ap.parse_args()

    try:
        envelope = json.loads(args.payload)
        payload = _verify_envelope(envelope)
        policy = _load_policy()
        if args.action == "decrypt":
            _policy_guard(
                action="decrypt",
                output_dir=Path(payload["output_dir"]),
                sandbox_root=Path(payload["sandbox_root"]),
                policy=policy,
            )
            out = _action_decrypt(payload)
        else:
            raise ValueError(f"Unsupported action: {args.action}")
        print(json.dumps({"ok": True, "result": out}))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
