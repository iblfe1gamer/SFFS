"""
Standalone mock-based cloud backup test.
No Google credentials required.
Run: python scripts/test_cloud_backup_mock.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_CODE3 = _ROOT / "code3"
if str(_CODE3) not in sys.path:
    sys.path.insert(0, str(_CODE3))

import f16_cloud_sync as cloud_mod

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    status = "PASS" if cond else "FAIL"
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{status}] {name}{suffix}")
    if cond:
        PASS += 1
    else:
        FAIL += 1


# ── Shared mock infrastructure ────────────────────────────────────────────────

class DummyCreds:
    valid = True
    expired = False
    refresh_token = None


class FakeFilesApi:
    """Tracks calls; returns configurable responses."""

    def __init__(self, folder_id="folder-1", upload_id="file-abc"):
        self._folder_id = folder_id
        self._upload_id = upload_id
        self.deleted = []
        self._files = []

    def list(self, q=None, spaces=None, fields=None):
        class _Exec:
            def __init__(self, data):
                self._data = data
            def execute(self):
                return self._data
        # folder lookup vs file listing
        if "mimeType" in (q or ""):
            return _Exec({"files": [{"id": self._folder_id, "name": cloud_mod.BACKUP_FOLDER_NAME}]})
        return _Exec({"files": self._files})

    def create(self, body=None, media_body=None, fields=None):
        class _Exec:
            def __init__(self, result):
                self._result = result
            def execute(self):
                return self._result
        if body and body.get("mimeType") == "application/vnd.google-apps.folder":
            return _Exec({"id": self._folder_id})
        name = body.get("name", "unknown") if body else "unknown"
        self._files.append({"id": self._upload_id, "name": name,
                             "size": "14", "modifiedTime": "2026-01-01T00:00:00Z"})
        return _Exec({"id": self._upload_id, "name": name})

    def delete(self, fileId=None):
        self.deleted.append(fileId)
        self._files = [f for f in self._files if f["id"] != fileId]
        class _Exec:
            @staticmethod
            def execute():
                return None
        return _Exec()

    def get_media(self, fileId=None):
        import io
        from unittest.mock import MagicMock
        req = MagicMock()
        return req


class FakeService:
    def __init__(self, **kw):
        self._api = FakeFilesApi(**kw)
    def files(self):
        return self._api


def _patch(monkeydict: dict):
    """Apply patches stored as {attr: value} on cloud_mod."""
    originals = {}
    for k, v in monkeydict.items():
        originals[k] = getattr(cloud_mod, k, None)
        setattr(cloud_mod, k, v)
    return originals


def _restore(originals: dict):
    for k, v in originals.items():
        setattr(cloud_mod, k, v)


# ── Tests ────────────────────────────────────────────────────────────────────

def test_no_google_libs(tmp_path: Path) -> None:
    print("\n-- no_google_libs --")
    orig = _patch({"_GOOGLE_OK": False})
    try:
        r = cloud_mod.cloudSync("list", config_dir=tmp_path)
        check("returns offline status", r["status"] == "offline")
        check("message present", "not installed" in r.get("message", ""))
    finally:
        _restore(orig)


def test_no_config_dir() -> None:
    print("\n-- no_config_dir --")
    orig = _patch({"_GOOGLE_OK": True})
    try:
        r = cloud_mod.cloudSync("list")
        check("returns not_authenticated", r["status"] == "not_authenticated")
    finally:
        _restore(orig)


def test_no_token(tmp_path: Path) -> None:
    print("\n-- no_token --")
    orig = _patch({"_GOOGLE_OK": True, "loadCredentials": lambda d: None})
    try:
        r = cloud_mod.cloudSync("list", config_dir=tmp_path)
        check("returns not_authenticated", r["status"] == "not_authenticated")
    finally:
        _restore(orig)


def test_upload(tmp_path: Path) -> None:
    print("\n-- upload --")
    src = tmp_path / "keys_backup.zip"
    src.write_bytes(b"encrypted-blob")
    svc = FakeService()
    orig = _patch({
        "_GOOGLE_OK": True,
        "loadCredentials": lambda d: DummyCreds(),
        "build": lambda *a, **k: svc,
        "MediaFileUpload": lambda path, resumable=True: object(),
    })
    try:
        r = cloud_mod.cloudSync("upload", local_path=src, config_dir=tmp_path)
        check("status=uploaded", r["status"] == "uploaded", r.get("status"))
        check("file_id present", bool(r.get("file_id")))
        check("drive_path present", bool(r.get("drive_path")))
    finally:
        _restore(orig)


def test_upload_missing_file(tmp_path: Path) -> None:
    print("\n-- upload_missing_file --")
    missing = tmp_path / "nonexistent.zip"
    orig = _patch({
        "_GOOGLE_OK": True,
        "loadCredentials": lambda d: DummyCreds(),
        "build": lambda *a, **k: FakeService(),
    })
    try:
        r = cloud_mod.cloudSync("upload", local_path=missing, config_dir=tmp_path)
        check("status=error", r["status"] == "error")
        check("message mentions file", "file" in r.get("message", ""))
    finally:
        _restore(orig)


def test_upload_blocks_unencrypted_keystore(tmp_path: Path) -> None:
    print("\n-- upload_blocks_unencrypted_keystore --")
    bad = tmp_path / "keystore.json"
    # Has version but missing kdf/encrypted_private_key/etc
    bad.write_text(json.dumps({"version": 1, "public_key": "abc"}), encoding="utf-8")
    orig = _patch({
        "_GOOGLE_OK": True,
        "loadCredentials": lambda d: DummyCreds(),
        "build": lambda *a, **k: FakeService(),
    })
    try:
        r = cloud_mod.cloudSync("upload", local_path=bad, config_dir=tmp_path)
        check("status=error", r["status"] == "error")
        check("message mentions unencrypted", "unencrypted" in r.get("message", "").lower()
              or "missing" in r.get("message", "").lower())
    finally:
        _restore(orig)


def test_upload_allows_encrypted_keystore(tmp_path: Path) -> None:
    print("\n-- upload_allows_encrypted_keystore --")
    good = tmp_path / "keystore.json"
    good.write_text(json.dumps({
        "version": 1,
        "kdf": "argon2id",
        "encrypted_private_key": "abc",
        "auth_tag": "xyz",
        "iv": "000",
        "salt": "111",
    }), encoding="utf-8")
    svc = FakeService()
    orig = _patch({
        "_GOOGLE_OK": True,
        "loadCredentials": lambda d: DummyCreds(),
        "build": lambda *a, **k: svc,
        "MediaFileUpload": lambda path, resumable=True: object(),
    })
    try:
        r = cloud_mod.cloudSync("upload", local_path=good, config_dir=tmp_path)
        check("status=uploaded", r["status"] == "uploaded")
    finally:
        _restore(orig)


def test_list(tmp_path: Path) -> None:
    print("\n-- list --")
    svc = FakeService()
    # Pre-populate a file
    svc.files()._files = [{"id": "x1", "name": "sffs_test.zip", "size": "100",
                           "modifiedTime": "2026-01-01T00:00:00Z"}]
    orig = _patch({
        "_GOOGLE_OK": True,
        "loadCredentials": lambda d: DummyCreds(),
        "build": lambda *a, **k: svc,
    })
    try:
        r = cloud_mod.cloudSync("list", config_dir=tmp_path)
        check("status=ok", r["status"] == "ok")
        check("files is list", isinstance(r.get("files"), list))
        check("file entry has file_id", r["files"][0].get("file_id") == "x1")
    finally:
        _restore(orig)


def test_delete(tmp_path: Path) -> None:
    print("\n-- delete --")
    svc = FakeService()
    orig = _patch({
        "_GOOGLE_OK": True,
        "loadCredentials": lambda d: DummyCreds(),
        "build": lambda *a, **k: svc,
    })
    try:
        r = cloud_mod.cloudSync("delete", file_id="file-abc", config_dir=tmp_path)
        check("status=deleted", r["status"] == "deleted")
        check("file_id echoed", r.get("file_id") == "file-abc")
        check("delete called on api", "file-abc" in svc.files().deleted)
    finally:
        _restore(orig)


def test_delete_no_file_id(tmp_path: Path) -> None:
    print("\n-- delete_no_file_id --")
    orig = _patch({
        "_GOOGLE_OK": True,
        "loadCredentials": lambda d: DummyCreds(),
        "build": lambda *a, **k: FakeService(),
    })
    try:
        r = cloud_mod.cloudSync("delete", config_dir=tmp_path)
        check("status=error", r["status"] == "error")
    finally:
        _restore(orig)


def test_unknown_action(tmp_path: Path) -> None:
    print("\n-- unknown_action --")
    orig = _patch({
        "_GOOGLE_OK": True,
        "loadCredentials": lambda d: DummyCreds(),
        "build": lambda *a, **k: FakeService(),
    })
    try:
        r = cloud_mod.cloudSync("frobnicate", config_dir=tmp_path)
        check("status=error", r["status"] == "error")
        check("message mentions action", "frobnicate" in r.get("message", ""))
    finally:
        _restore(orig)


def test_expired_token_refresh(tmp_path: Path) -> None:
    print("\n-- expired_token_refresh --")

    refreshed = []

    class ExpiredCreds:
        valid = False
        expired = True
        refresh_token = "rtoken"
        def refresh(self, req):
            refreshed.append(True)
            self.valid = True
            self.expired = False
        def to_json(self):
            return json.dumps({"token": "new"})

    svc = FakeService()
    orig = _patch({
        "_GOOGLE_OK": True,
        "loadCredentials": lambda d: ExpiredCreds(),
        "build": lambda *a, **k: svc,
        "Request": lambda: None,
    })
    try:
        r = cloud_mod.cloudSync("list", config_dir=tmp_path)
        check("token refresh called", len(refreshed) == 1)
        check("status=ok after refresh", r["status"] == "ok")
    finally:
        _restore(orig)


def _ensure_sffs_paths() -> None:
    for d in ("code1", "code2", "code3", "main-code"):
        p = str(_ROOT / d)
        if p not in sys.path:
            sys.path.insert(0, p)


def test_restore_keys_from_cloud(tmp_path: Path) -> None:
    print("\n-- restore_keys_from_cloud --")
    _ensure_sffs_paths()
    from sffs_core import SFFSCore

    keys_dir = tmp_path / "keys"
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Build a zip with fake key files
    import zipfile, io
    zip_buf = io.BytesIO()
    key_files = {
        "keystore_abc.json": b'{"version":1,"kdf":"argon2id","encrypted_private_key":"x","auth_tag":"x","iv":"x","salt":"x"}',
        "public_key_abc.pem": b"-----BEGIN PUBLIC KEY-----",
        "wrap_store.enc": b'{"iv":"aaa","ciphertext":"bbb","tag":"ccc"}',
        "wrap_store.salt": b"\x00" * 16,
    }
    with zipfile.ZipFile(zip_buf, "w") as zf:
        for name, data in key_files.items():
            zf.writestr(name, data)
    zip_bytes = zip_buf.getvalue()

    # Mock cloudSync("download") to write the zip to local_path
    def fake_cloud_sync(action, file_id=None, local_path=None, config_dir=None, **kw):
        if action == "download":
            Path(local_path).write_bytes(zip_bytes)
            return {"status": "downloaded", "local_path": local_path}
        return {"status": "error", "message": "unexpected action"}

    # Patch cloudSync in sffs_core's module namespace
    import sffs_core as core_mod
    orig_cs = core_mod.cloudSync
    core_mod.cloudSync = fake_cloud_sync

    try:
        core = SFFSCore()
        result = core.restoreKeysFromCloud("file-123", config_dir, keys_dir)
        check("status=restored", result.get("status") == "restored", result.get("status"))
        check("keys_dir path returned", str(keys_dir) in result.get("keys_dir", ""))
        check("keystore extracted", (keys_dir / "keystore_abc.json").exists())
        check("public key extracted", (keys_dir / "public_key_abc.pem").exists())
        check("wrap_store.enc extracted", (keys_dir / "wrap_store.enc").exists())
        check("wrap_store.salt extracted", (keys_dir / "wrap_store.salt").exists())
    finally:
        core_mod.cloudSync = orig_cs


def test_restore_rejects_path_traversal(tmp_path: Path) -> None:
    print("\n-- restore_rejects_path_traversal --")
    import zipfile, io
    _ensure_sffs_paths()
    from sffs_core import SFFSCore
    import sffs_core as core_mod

    keys_dir = tmp_path / "keys"
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Zip with a traversal path
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("../evil.sh", b"rm -rf /")
    zip_bytes = zip_buf.getvalue()

    def fake_download(action, file_id=None, local_path=None, config_dir=None, **kw):
        Path(local_path).write_bytes(zip_bytes)
        return {"status": "downloaded", "local_path": local_path}

    orig_cs = core_mod.cloudSync
    core_mod.cloudSync = fake_download
    try:
        core = SFFSCore()
        result = core.restoreKeysFromCloud("file-x", config_dir, keys_dir)
        check("path traversal blocked", result.get("status") == "error")
        check("message mentions unsafe", "unsafe" in result.get("message", "").lower()
              or "path" in result.get("message", "").lower())
    finally:
        core_mod.cloudSync = orig_cs


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    tests = [
        test_no_google_libs,
        test_no_config_dir,
        test_no_token,
        test_upload,
        test_upload_missing_file,
        test_upload_blocks_unencrypted_keystore,
        test_upload_allows_encrypted_keystore,
        test_list,
        test_delete,
        test_delete_no_file_id,
        test_unknown_action,
        test_expired_token_refresh,
        test_restore_keys_from_cloud,
        test_restore_rejects_path_traversal,
    ]

    for t in tests:
        import inspect
        sig = inspect.signature(t)
        if sig.parameters:
            with tempfile.TemporaryDirectory() as td:
                t(Path(td))
        else:
            t()

    print(f"\n{'='*40}")
    print(f"  PASS: {PASS}  FAIL: {FAIL}  TOTAL: {PASS+FAIL}")
    print(f"  OVERALL: {'PASS' if FAIL == 0 else 'FAIL'}")
    print(f"{'='*40}")
    sys.exit(0 if FAIL == 0 else 1)
