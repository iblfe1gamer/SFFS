"""Hardening tests for isolated worker IPC and policy checks."""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
import time
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_MAIN = _ROOT / "main-code"
if str(_MAIN) not in sys.path:
    sys.path.insert(0, str(_MAIN))

import isolated_worker as iw


def _sign_envelope(ipc_key: str, payload: dict, nonce: str = "n1", session_token: str = "s1", issued_at: int | None = None) -> dict:
    if issued_at is None:
        issued_at = int(time.time())
    envelope = {
        "payload": payload,
        "nonce": nonce,
        "session_token": session_token,
        "issued_at": issued_at,
    }
    msg = json.dumps(envelope, sort_keys=True, separators=(",", ":"))
    envelope["signature"] = hmac.new(ipc_key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()
    return envelope


def test_verify_envelope_accepts_valid_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SFFS_IPC_KEY", "k_test")
    payload = {"output_dir": "x", "sandbox_root": "y"}
    env = _sign_envelope("k_test", payload)
    out = iw._verify_envelope(env)
    assert out == payload


def test_verify_envelope_rejects_tampered_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SFFS_IPC_KEY", "k_test")
    payload = {"output_dir": "x", "sandbox_root": "y"}
    env = _sign_envelope("k_test", payload)
    env["signature"] = "00" * 32
    with pytest.raises(PermissionError):
        iw._verify_envelope(env)


def test_verify_envelope_rejects_stale_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SFFS_IPC_KEY", "k_test")
    payload = {"output_dir": "x", "sandbox_root": "y"}
    env = _sign_envelope("k_test", payload, issued_at=int(time.time()) - 120)
    with pytest.raises(PermissionError):
        iw._verify_envelope(env)


def test_policy_guard_rejects_wrong_output_root(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    wrong_out = sandbox / "not-decrypted"
    policy = {"allowed_actions": ["decrypt"], "output_root_relative": "decrypted"}
    with pytest.raises(PermissionError):
        iw._policy_guard("decrypt", wrong_out, sandbox, policy)


def test_policy_guard_rejects_disallowed_action(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    out_dir = sandbox / "decrypted"
    out_dir.mkdir(parents=True)
    policy = {"allowed_actions": ["decrypt"], "output_root_relative": "decrypted"}
    with pytest.raises(PermissionError):
        iw._policy_guard("encrypt", out_dir, sandbox, policy)


def test_require_within_rejects_escape(tmp_path: Path) -> None:
    parent = tmp_path / "sandbox"
    parent.mkdir()
    outsider = tmp_path / "elsewhere"
    outsider.mkdir()
    with pytest.raises(PermissionError):
        iw._require_within(outsider, parent)

