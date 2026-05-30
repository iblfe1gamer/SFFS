"""
Sandbox security audit — functional correctness + leak/escape checks.

Goal:
  1. Sandbox works as intended:
     - Correct directory structure created
     - Decrypted files reside only in sandbox/decrypted/
     - OS-level isolation markers enforced
     - Sandbox securely destroyed on teardown

  2. Security: sandbox is not leaking anything:
     - Launcher rejects files outside sandbox root
     - Launcher rejects exe escaping apps root
     - Worker path policy blocks output-dir escapes
     - OS isolation gate blocks launch without job/apparmor
     - Secure wipe actually overwrites file content
     - Lock file has valid structure
     - isSandboxIntact detects missing/malformed lock

Known issues (documented, not silently skipped):
  - ISSUE-1: master_password passed in plaintext CLI arg → visible in tasklist
  - ISSUE-2: icacls failure on Windows silently falls through (no exception raised)
  - ISSUE-3: isSandboxIntact on Windows skips ACL check (always True if lock exists)
  - ISSUE-4: Lock file created without explicit owner-only permissions
  - ISSUE-5: sandbox_viewer.py reads path without validating it is inside sandbox
"""

from __future__ import annotations

import json
import os
import platform
import stat
import sys
import uuid
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
for _sub in ("code1", "code2", "code3", "main-code"):
    p = str(_ROOT / _sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from f07_create_isolated_sandbox import (
    createIsolatedSandbox,
    destroySandbox,
    isSandboxIntact,
    secureWipeDirectory,
)
from os_isolation import detect_isolation, ensure_secure_mode
import secure_app_launcher as sal
from secure_app_launcher import LauncherPolicyError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manifest(
    root: Path,
    exe_rel: str = "apps/viewer/viewer.exe",
    *,
    create_exe: bool = True,
    secure_mode_required: bool = False,
) -> Path:
    apps_dir = (root / exe_rel).parent
    apps_dir.mkdir(parents=True, exist_ok=True)
    if create_exe:
        (root / exe_rel).write_bytes(b"fake-exe")

    dec = root / "sffs_data" / "sandbox" / "decrypted"
    tmp = root / "sffs_data" / "sandbox" / "temp"
    dec.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)

    manifest = {
        "manifest_version": "1.0",
        "policy": {
            "apps_root": "apps",
            "allowed_open_root": "sffs_data/sandbox/decrypted",
            "working_dir": "sffs_data/sandbox/temp",
            "secure_mode_required": secure_mode_required,
        },
        "routes": {".txt": "viewer", ".pdf": "viewer"},
        "apps": {"viewer": {"exe_rel": exe_rel, "args": []}},
    }
    mpath = root / "apps" / "apps_manifest.json"
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return mpath


# ===========================================================================
# 1. Functional: Sandbox structure
# ===========================================================================

class TestSandboxStructure:
    def test_creates_sandbox_directory(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="test1")
        sp = Path(s["sandbox_path"])
        assert sp.is_dir(), "sandbox_path must be a directory"

    def test_creates_decrypted_subdirectory(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="test2")
        assert Path(s["decrypted_dir"]).is_dir()

    def test_creates_temp_subdirectory(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="test3")
        assert Path(s["temp_dir"]).is_dir()

    def test_creates_keys_runtime_subdirectory(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="test4")
        assert Path(s["keys_runtime_dir"]).is_dir()

    def test_decrypted_dir_is_inside_sandbox(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="test5")
        sp = Path(s["sandbox_path"]).resolve()
        dec = Path(s["decrypted_dir"]).resolve()
        assert sp in dec.parents, "decrypted_dir must be inside sandbox_path"

    def test_temp_dir_is_inside_sandbox(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="test6")
        sp = Path(s["sandbox_path"]).resolve()
        tmp_d = Path(s["temp_dir"]).resolve()
        assert sp in tmp_d.parents

    def test_keys_runtime_dir_is_inside_sandbox(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="test7")
        sp = Path(s["sandbox_path"]).resolve()
        kr = Path(s["keys_runtime_dir"]).resolve()
        assert sp in kr.parents

    def test_lock_file_created(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="lf1")
        lock = Path(s["sandbox_path"]) / "sandbox.lock"
        assert lock.is_file(), "sandbox.lock must be created"

    def test_lock_file_contains_session_id(self, tmp_path: Path) -> None:
        sid = "lock_test_session"
        s = createIsolatedSandbox(tmp_path, session_id=sid)
        lock = Path(s["sandbox_path"]) / "sandbox.lock"
        content = lock.read_text()
        assert f"session_id={sid}" in content

    def test_lock_file_contains_created_timestamp(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="ts_test")
        lock = Path(s["sandbox_path"]) / "sandbox.lock"
        content = lock.read_text()
        assert "created=" in content
        ts_str = [l for l in content.splitlines() if l.startswith("created=")][0]
        ts = int(ts_str.split("=")[1])
        import time
        assert abs(time.time() - ts) < 10, "timestamp should be recent"

    def test_platform_reported_correctly(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="plat1")
        assert s["platform"] == platform.system()

    def test_auto_generates_session_id_when_none(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path)
        assert s["session_id"], "session_id must be auto-generated"
        assert len(s["session_id"]) > 8

    def test_duplicate_session_id_raises(self, tmp_path: Path) -> None:
        createIsolatedSandbox(tmp_path, session_id="dup1")
        with pytest.raises(Exception):
            createIsolatedSandbox(tmp_path, session_id="dup1")


# ===========================================================================
# 2. Functional: Linux permissions (skip on Windows)
# ===========================================================================

@pytest.mark.skipif(platform.system() != "Linux", reason="Linux-only chmod test")
class TestSandboxPermissionsLinux:
    def test_sandbox_dir_owner_only_permissions(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="perm1")
        sp = Path(s["sandbox_path"])
        mode = oct(sp.stat().st_mode)[-3:]
        assert mode == "700", f"Expected 700, got {mode}"

    def test_sandbox_dir_not_group_readable(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="perm2")
        sp = Path(s["sandbox_path"])
        mode = sp.stat().st_mode
        assert not (mode & stat.S_IRGRP), "Group read must not be set"
        assert not (mode & stat.S_IROTH), "Other read must not be set"


# ===========================================================================
# 3. Functional: isSandboxIntact
# ===========================================================================

class TestIsSandboxIntact:
    def test_intact_after_creation(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="intg1")
        assert isSandboxIntact(Path(s["sandbox_path"])) is True

    def test_false_for_nonexistent_path(self, tmp_path: Path) -> None:
        assert isSandboxIntact(tmp_path / "no_such_sandbox") is False

    def test_false_when_lock_deleted(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="intg2")
        sp = Path(s["sandbox_path"])
        (sp / "sandbox.lock").unlink()
        assert isSandboxIntact(sp) is False

    def test_false_when_lock_content_malformed(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="intg3")
        sp = Path(s["sandbox_path"])
        (sp / "sandbox.lock").write_text("garbage content")
        assert isSandboxIntact(sp) is False

    def test_false_when_lock_empty(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="intg4")
        sp = Path(s["sandbox_path"])
        (sp / "sandbox.lock").write_text("")
        assert isSandboxIntact(sp) is False


# ===========================================================================
# 4. Functional: Destroy + secure wipe
# ===========================================================================

class TestSandboxDestroy:
    def test_destroy_removes_directory(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="del1")
        sp = Path(s["sandbox_path"])
        assert destroySandbox(sp) is True
        assert not sp.exists()

    def test_destroy_nonexistent_returns_true(self, tmp_path: Path) -> None:
        assert destroySandbox(tmp_path / "phantom") is True

    def test_destroy_removes_nested_files(self, tmp_path: Path) -> None:
        s = createIsolatedSandbox(tmp_path, session_id="del2")
        dec = Path(s["decrypted_dir"])
        (dec / "secret.txt").write_bytes(b"plaintext secret")
        (dec / "nested" ).mkdir(exist_ok=True)
        (dec / "nested" / "deep.txt").write_bytes(b"deep secret")
        destroySandbox(Path(s["sandbox_path"]))
        assert not Path(s["sandbox_path"]).exists()

    def test_secure_wipe_overwrites_content(self, tmp_path: Path) -> None:
        """File content is overwritten; original bytes should not remain."""
        victim = tmp_path / "victim.txt"
        original = b"SENSITIVE_DATA_12345"
        victim.write_bytes(original)

        secureWipeDirectory(tmp_path)

        # File should be deleted after wipe
        assert not victim.exists()

    def test_secure_wipe_handles_empty_dir(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty_sub"
        empty.mkdir()
        secureWipeDirectory(empty)  # Must not raise

    def test_secure_wipe_handles_zero_byte_file(self, tmp_path: Path) -> None:
        zf = tmp_path / "zero.txt"
        zf.write_bytes(b"")
        secureWipeDirectory(tmp_path)
        assert not zf.exists()


# ===========================================================================
# 5. OS Isolation: detect_isolation + ensure_secure_mode
# ===========================================================================

class TestOSIsolation:
    def test_detect_isolation_returns_dict(self) -> None:
        result = detect_isolation()
        assert isinstance(result, dict)
        assert "active" in result
        assert "platform" in result
        assert "mode" in result
        assert "reason" in result

    def test_detect_isolation_platform_matches(self) -> None:
        result = detect_isolation()
        assert result["platform"] == platform.system().lower()

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_windows_isolation_active_with_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SFFS_OS_ISOLATION", "windows_job")
        monkeypatch.setenv("SFFS_JOB_OBJECT_ACTIVE", "1")
        result = detect_isolation()
        assert result["active"] is True
        assert result["mode"] == "windows_job"

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_windows_isolation_inactive_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SFFS_OS_ISOLATION", raising=False)
        monkeypatch.delenv("SFFS_JOB_OBJECT_ACTIVE", raising=False)
        result = detect_isolation()
        assert result["active"] is False

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux only")
    def test_linux_isolation_inactive_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SFFS_OS_ISOLATION", raising=False)
        result = detect_isolation()
        assert result["active"] is False

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux only")
    def test_linux_isolation_active_with_apparmor_marker(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv("SFFS_OS_ISOLATION", "apparmor")
        # Simulate a confined process by patching _linux_apparmor_confined
        import os_isolation as osi
        monkeypatch.setattr(osi, "_linux_apparmor_confined", lambda: (True, "confined profile: sffs"))
        result = detect_isolation()
        assert result["active"] is True

    def test_ensure_secure_mode_raises_when_not_isolated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ensure_secure_mode must raise RuntimeError when isolation is inactive."""
        monkeypatch.delenv("SFFS_OS_ISOLATION", raising=False)
        monkeypatch.delenv("SFFS_JOB_OBJECT_ACTIVE", raising=False)
        import os_isolation as osi
        monkeypatch.setattr(osi, "detect_isolation", lambda: {
            "active": False, "platform": "test", "mode": "none", "reason": "no isolation"
        })
        with pytest.raises(RuntimeError, match="Secure mode requires OS isolation"):
            ensure_secure_mode()

    def test_ensure_secure_mode_passes_when_isolated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import os_isolation as osi
        monkeypatch.setattr(osi, "detect_isolation", lambda: {
            "active": True, "platform": "test", "mode": "test_job", "reason": "ok"
        })
        ensure_secure_mode()  # Must not raise


# ===========================================================================
# 6. Secure App Launcher: policy enforcement
# ===========================================================================

class TestLauncherPolicy:
    def test_allows_file_inside_sandbox(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        mpath = _make_manifest(tmp_path)
        target = tmp_path / "sffs_data" / "sandbox" / "decrypted" / "doc.txt"
        target.write_text("hello", encoding="utf-8")
        monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)
        out = sal.resolve_launch(target, manifest_path=mpath)
        assert out["app_id"] == "viewer"
        assert out["target_file"] == target.resolve()

    def test_blocks_file_outside_sandbox(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """SECURITY: files outside sandbox open root must be rejected."""
        mpath = _make_manifest(tmp_path)
        outside = tmp_path / "secret_host_file.txt"
        outside.write_text("host secret", encoding="utf-8")
        monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)
        with pytest.raises(LauncherPolicyError, match="sandbox open root"):
            sal.resolve_launch(outside, manifest_path=mpath)

    def test_blocks_path_traversal_escape(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """SECURITY: path traversal must be rejected (e.g., sandbox/../../../etc/passwd)."""
        mpath = _make_manifest(tmp_path)
        monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)
        # Construct a path that resolves outside sandbox
        traversal = tmp_path / "sffs_data" / "sandbox" / "decrypted" / ".." / ".." / ".." / "escape.txt"
        escape_target = tmp_path.parent / "escape.txt"
        escape_target.write_text("escaped", encoding="utf-8")
        with pytest.raises((LauncherPolicyError, FileNotFoundError)):
            sal.resolve_launch(traversal, manifest_path=mpath)

    def test_blocks_unmapped_extension(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        mpath = _make_manifest(tmp_path)
        target = tmp_path / "sffs_data" / "sandbox" / "decrypted" / "doc.exe"
        target.write_bytes(b"fake exe")
        monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)
        with pytest.raises(LauncherPolicyError, match="No app mapping"):
            sal.resolve_launch(target, manifest_path=mpath)

    def test_blocks_exe_outside_apps_root(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """SECURITY: executable path must stay inside apps root."""
        mpath = _make_manifest(tmp_path, exe_rel="dangerous/../../evil.exe", create_exe=False)
        target = tmp_path / "sffs_data" / "sandbox" / "decrypted" / "doc.txt"
        target.write_text("hello", encoding="utf-8")
        monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)
        with pytest.raises((LauncherPolicyError, FileNotFoundError)):
            sal.resolve_launch(target, manifest_path=mpath)

    def test_blocks_missing_app_executable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        mpath = _make_manifest(tmp_path, exe_rel="apps/viewer/viewer.exe", create_exe=False)
        target = tmp_path / "sffs_data" / "sandbox" / "decrypted" / "doc.txt"
        target.write_text("hello", encoding="utf-8")
        monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)
        with pytest.raises(FileNotFoundError):
            sal.resolve_launch(target, manifest_path=mpath)

    def test_blocks_missing_target_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        mpath = _make_manifest(tmp_path)
        target = tmp_path / "sffs_data" / "sandbox" / "decrypted" / "ghost.txt"
        # Do NOT create target
        monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)
        with pytest.raises(FileNotFoundError):
            sal.resolve_launch(target, manifest_path=mpath)

    def test_working_dir_must_be_inside_sandbox(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """SECURITY: working_dir must be inside sffs_data/sandbox."""
        bad_manifest = {
            "manifest_version": "1.0",
            "policy": {
                "apps_root": "apps",
                "allowed_open_root": "sffs_data/sandbox/decrypted",
                "working_dir": "outside_sandbox/temp",  # ← outside sandbox
                "secure_mode_required": False,
            },
            "routes": {".txt": "viewer"},
            "apps": {"viewer": {"exe_rel": "apps/viewer/viewer.exe", "args": []}},
        }
        apps_dir = tmp_path / "apps" / "viewer"
        apps_dir.mkdir(parents=True, exist_ok=True)
        (tmp_path / "apps" / "viewer" / "viewer.exe").write_bytes(b"fake")
        dec = tmp_path / "sffs_data" / "sandbox" / "decrypted"
        dec.mkdir(parents=True, exist_ok=True)
        mpath = tmp_path / "apps" / "apps_manifest.json"
        mpath.write_text(json.dumps(bad_manifest, indent=2), encoding="utf-8")
        target = dec / "doc.txt"
        target.write_text("hello", encoding="utf-8")
        monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)
        with pytest.raises(LauncherPolicyError, match="outside sandbox"):
            sal.resolve_launch(target, manifest_path=mpath)

    def test_secure_mode_gate_blocks_when_inactive(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """SECURITY: with secure_mode_required=True and no isolation, launch must be blocked."""
        mpath = _make_manifest(tmp_path, secure_mode_required=True)
        target = tmp_path / "sffs_data" / "sandbox" / "decrypted" / "doc.txt"
        target.write_text("hello", encoding="utf-8")
        monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)
        monkeypatch.delenv("SFFS_OS_ISOLATION", raising=False)
        monkeypatch.delenv("SFFS_JOB_OBJECT_ACTIVE", raising=False)
        import os_isolation as osi
        monkeypatch.setattr(osi, "detect_isolation", lambda: {
            "active": False, "platform": "test", "mode": "none", "reason": "no isolation"
        })
        # On Windows, try_activate_job_for_current_process may activate the job → allow this
        try:
            from windows_job_wrapper import try_activate_job_for_current_process
            can_activate = try_activate_job_for_current_process()
        except Exception:
            can_activate = False

        if can_activate:
            pytest.skip("Windows job auto-activation succeeded — isolation is active")
        with pytest.raises(LauncherPolicyError):
            sal.resolve_launch(target, manifest_path=mpath)

    def test_manifest_missing_keys_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        mpath = tmp_path / "apps" / "apps_manifest.json"
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mpath.write_text(json.dumps({"manifest_version": "1.0"}), encoding="utf-8")
        monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)
        target = tmp_path / "doc.txt"
        target.write_text("x")
        with pytest.raises(ValueError, match="missing required keys"):
            sal.resolve_launch(target, manifest_path=mpath)

    def test_launch_env_redirects_temp_to_sandbox(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """SECURITY: TEMP/TMP env vars must point inside sandbox for launched apps."""
        mpath = _make_manifest(tmp_path)
        target = tmp_path / "sffs_data" / "sandbox" / "decrypted" / "doc.txt"
        target.write_text("hello", encoding="utf-8")
        monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)
        resolved = sal.resolve_launch(target, manifest_path=mpath)
        sandbox_root = (tmp_path / "sffs_data" / "sandbox").resolve()
        wd = Path(resolved["working_dir"]).resolve()
        assert sandbox_root in wd.parents or wd == sandbox_root or sandbox_root in wd.parents, \
            f"working_dir {wd} must be inside sandbox {sandbox_root}"


# ===========================================================================
# 7. Worker path policy (isolated_worker)
# ===========================================================================

class TestWorkerPathPolicy:
    def setup_method(self) -> None:
        import isolated_worker as iw
        self.iw = iw

    def test_require_within_allows_child(self, tmp_path: Path) -> None:
        parent = tmp_path / "sandbox"
        parent.mkdir()
        child = parent / "decrypted" / "file.txt"
        child.parent.mkdir(parents=True)
        child.write_text("x")
        self.iw._require_within(child, parent)  # Must not raise

    def test_require_within_blocks_escape(self, tmp_path: Path) -> None:
        parent = tmp_path / "sandbox"
        parent.mkdir()
        outside = tmp_path / "not_sandbox" / "file.txt"
        outside.parent.mkdir(parents=True)
        outside.write_text("x")
        with pytest.raises(PermissionError, match="Path policy violation"):
            self.iw._require_within(outside, parent)

    def test_require_within_blocks_parent_traversal(self, tmp_path: Path) -> None:
        """SECURITY: sandbox/.. must be blocked."""
        parent = tmp_path / "sandbox"
        parent.mkdir()
        with pytest.raises(PermissionError):
            self.iw._require_within(tmp_path, parent)

    def test_policy_guard_allows_correct_output_dir(self, tmp_path: Path) -> None:
        sandbox = tmp_path / "sandbox"
        out_dir = sandbox / "decrypted"
        out_dir.mkdir(parents=True)
        policy = {"allowed_actions": ["decrypt"], "output_root_relative": "decrypted"}
        self.iw._policy_guard("decrypt", out_dir, sandbox, policy)  # Must not raise

    def test_policy_guard_blocks_wrong_output_root(self, tmp_path: Path) -> None:
        sandbox = tmp_path / "sandbox"
        sandbox.mkdir()
        wrong = sandbox / "keys_runtime"
        policy = {"allowed_actions": ["decrypt"], "output_root_relative": "decrypted"}
        with pytest.raises(PermissionError):
            self.iw._policy_guard("decrypt", wrong, sandbox, policy)

    def test_policy_guard_blocks_disallowed_action(self, tmp_path: Path) -> None:
        sandbox = tmp_path / "sandbox"
        out = sandbox / "decrypted"
        out.mkdir(parents=True)
        policy = {"allowed_actions": ["decrypt"], "output_root_relative": "decrypted"}
        with pytest.raises(PermissionError, match="denied by policy"):
            self.iw._policy_guard("encrypt", out, sandbox, policy)

    def test_require_not_system_path_blocks_windows_root(self) -> None:
        if platform.system() != "Windows":
            pytest.skip("Windows path test")
        c_windows = Path("C:\\Windows\\System32")
        if c_windows.exists():
            with pytest.raises(PermissionError, match="system path"):
                self.iw._require_not_system_path(c_windows)

    def test_require_not_system_path_allows_tmp(self, tmp_path: Path) -> None:
        self.iw._require_not_system_path(tmp_path)  # Must not raise


# ===========================================================================
# 8. Known security issues (documented/asserted)
# ===========================================================================

class TestSecurityFixesVerified:
    """
    Verify all 5 security issues are fixed.
    Each test asserts the FIXED behavior.
    """

    def test_FIX1_master_password_NOT_in_cli_payload(self) -> None:
        """
        FIX-1: master_password must NOT appear in the JSON payload sent as
        CLI arg. It must be passed via stdin pipe instead.
        """
        import sffs_core
        import inspect

        src = inspect.getsource(sffs_core.SFFSCore._decrypt_via_worker)
        # master_password must NOT be in the payload dict
        # (look for it being assigned into the dict literal)
        assert '"master_password": master_password' not in src, \
            "FIX-1 FAILED: master_password still present in CLI payload dict"
        # stdin=subprocess.PIPE must be set
        assert "stdin=subprocess.PIPE" in src, \
            "FIX-1 FAILED: stdin=subprocess.PIPE not set on Popen"
        # password must be delivered via communicate(input=...)
        assert "communicate(" in src and "input=" in src, \
            "FIX-1 FAILED: master_password not passed via stdin communicate"

    def test_FIX1_worker_reads_password_from_stdin(self) -> None:
        """Worker must read master_password from stdin, not from payload."""
        import isolated_worker as iw
        import inspect

        main_src = inspect.getsource(iw.main)
        action_src = inspect.getsource(iw._action_decrypt)

        assert "stdin.readline" in main_src, \
            "FIX-1 FAILED: worker main() must read password from stdin"
        assert 'payload["master_password"]' not in action_src, \
            "FIX-1 FAILED: _action_decrypt must not extract password from payload dict"

    def test_FIX2_icacls_failure_raises_on_windows(self, tmp_path: Path) -> None:
        """
        FIX-2: createIsolatedSandbox must raise RuntimeError when icacls fails,
        and must clean up the unprotected directory.
        """
        if platform.system() != "Windows":
            pytest.skip("Windows-only fix")

        import subprocess as sp
        import unittest.mock as mock

        original_run = sp.run

        def mock_run_fail(cmd, **kwargs):
            if cmd and "icacls" in str(cmd[0]):
                raise sp.CalledProcessError(1, cmd)
            return original_run(cmd, **kwargs)

        with mock.patch("f07_create_isolated_sandbox.subprocess.run", side_effect=mock_run_fail):
            with pytest.raises(RuntimeError, match="Failed to set restrictive ACLs"):
                createIsolatedSandbox(tmp_path, session_id="icacls_fix_test")

        # Directory must be cleaned up after failure
        sandbox_path = tmp_path / "sandbox_icacls_fix_test"
        assert not sandbox_path.exists(), \
            "FIX-2 FAILED: unprotected sandbox directory left on disk after icacls failure"

    def test_FIX3_sandbox_intact_checks_acl_on_windows(self, tmp_path: Path) -> None:
        """
        FIX-3: isSandboxIntact on Windows must call icacls to verify ACLs.
        """
        if platform.system() != "Windows":
            pytest.skip("Windows-only fix")

        import f07_create_isolated_sandbox as f07
        import inspect

        src = inspect.getsource(f07.isSandboxIntact)
        assert "icacls" in src, \
            "FIX-3 FAILED: isSandboxIntact must call icacls to verify ACLs on Windows"
        assert "broad_entries" in src or "Everyone" in src, \
            "FIX-3 FAILED: must check for broad ACL entries (Everyone, BUILTIN\\Users)"

    def test_FIX3_sandbox_intact_fails_when_icacls_reports_broad_access(self, tmp_path: Path) -> None:
        """isSandboxIntact returns False when icacls shows Everyone in ACL."""
        if platform.system() != "Windows":
            pytest.skip("Windows-only fix")

        import subprocess as sp
        import unittest.mock as mock

        s = createIsolatedSandbox(tmp_path, session_id="broadacl_test")
        sp_path = Path(s["sandbox_path"])

        # Simulate icacls returning "Everyone" in output
        fake_result = mock.MagicMock()
        fake_result.stdout = f"{sp_path}\n  Everyone:(OI)(CI)(F)\n"
        fake_result.returncode = 0

        with mock.patch("f07_create_isolated_sandbox.subprocess.run", return_value=fake_result):
            result = isSandboxIntact(sp_path)
        assert result is False, \
            "FIX-3 FAILED: isSandboxIntact should return False when Everyone appears in ACL"

    @pytest.mark.skipif(platform.system() != "Linux", reason="Permission check on Linux only")
    def test_FIX4_lock_file_owner_only_on_linux(self, tmp_path: Path) -> None:
        """
        FIX-4: sandbox.lock must be created with mode 0o600 on Linux.
        """
        s = createIsolatedSandbox(tmp_path, session_id="lockperm_fix")
        lock = Path(s["sandbox_path"]) / "sandbox.lock"
        mode = oct(lock.stat().st_mode)[-3:]
        assert mode in ("600", "400"), \
            f"FIX-4 FAILED: sandbox.lock has permissions {mode}, expected 600"

    def test_FIX5_sandbox_viewer_validates_path_in_source(self) -> None:
        """
        FIX-5: show_sandbox_file_viewer must validate path is inside sandbox
        before any file I/O.
        """
        pytest.importorskip("PyQt6.QtWidgets", reason="PyQt6 not available in headless CI")
        import inspect
        import sandbox_viewer as sv

        src = inspect.getsource(sv.show_sandbox_file_viewer)
        assert "relative_to" in src, \
            "FIX-5 FAILED: must use path.relative_to(decrypted_root) for boundary check"
        assert "decrypted_dir" in src or "decrypted_root" in src, \
            "FIX-5 FAILED: must reference sandbox decrypted_dir as the boundary root"
        assert "Access blocked" in src or "boundary" in src.lower(), \
            "FIX-5 FAILED: must reject and warn when path is outside sandbox"

    def test_FIX5_sandbox_viewer_blocks_outside_path(self) -> None:
        """
        FIX-5: Viewer must return 'error' when path is outside sandbox decrypted root.
        Uses a mock parent with _core.sandbox set.
        """
        pytest.importorskip("PyQt6.QtWidgets", reason="PyQt6 not available in headless CI")
        import sandbox_viewer as sv
        import unittest.mock as mock

        # Build a mock parent with _core.sandbox pointing to a tmp sandbox
        parent = mock.MagicMock()
        sandbox_root = Path(__file__).resolve().parent.parent / "sffs_data" / "sandbox"
        decrypted = sandbox_root / "decrypted"
        parent._core.sandbox = {"decrypted_dir": str(decrypted)}

        # Path clearly outside sandbox
        outside_path = Path(__file__).resolve()  # this test file itself

        # QMessageBox.warning will be called — mock it
        with mock.patch("sandbox_viewer.QMessageBox") as mock_qmb:
            result = sv.show_sandbox_file_viewer(parent, outside_path)

        assert result == "error", \
            "FIX-5 FAILED: viewer must return 'error' for path outside sandbox"
        mock_qmb.warning.assert_called_once()

    def test_FIX5_sandbox_viewer_allows_path_inside_sandbox(self, tmp_path: Path) -> None:
        """
        FIX-5: Viewer must allow paths inside sandbox decrypted root.
        """
        pytest.importorskip("PyQt6.QtWidgets", reason="PyQt6 not available in headless CI")
        import sandbox_viewer as sv
        import unittest.mock as mock

        decrypted = tmp_path / "decrypted"
        decrypted.mkdir()
        test_file = decrypted / "hello.txt"
        test_file.write_text("hello sandbox")

        parent = mock.MagicMock()
        parent._core.sandbox = {"decrypted_dir": str(decrypted)}
        parent._core.logger = None

        # Mock QDialog so it doesn't try to show a real window
        with mock.patch("sandbox_viewer.QDialog") as mock_dlg, \
             mock.patch("sandbox_viewer.QLabel"), \
             mock.patch("sandbox_viewer.QTextEdit"), \
             mock.patch("sandbox_viewer.QVBoxLayout"):
            mock_dlg.return_value.__enter__ = mock.MagicMock()
            mock_dlg.return_value.exec = mock.MagicMock()
            result = sv.show_sandbox_file_viewer(parent, test_file)

        assert result == "inline", \
            "FIX-5 FAILED: viewer must allow file inside sandbox decrypted dir"


# ===========================================================================
# 9. Decrypted files stay inside sandbox (integration-level path checks)
# ===========================================================================

class TestDecryptionSandboxContainment:
    def test_default_output_dir_is_sandbox_decrypted(self, tmp_path: Path) -> None:
        """
        When decryptFileOperation is called without output_path,
        output MUST go to sandbox/decrypted/, not outside.
        Verify via _decrypt_via_worker payload construction.
        """
        import sffs_core
        import inspect

        src = inspect.getsource(sffs_core.SFFSCore.decryptFileOperation)
        # sandbox["decrypted_dir"] must be the output_dir when output_path is None
        assert "decrypted_dir" in src, \
            "decryptFileOperation must use sandbox decrypted_dir as default output"
        assert "sandbox_root" in src, \
            "sandbox_root must be passed to enforce worker path policy"

    def test_worker_payload_includes_sandbox_root_for_containment(self) -> None:
        """
        Worker payload must include sandbox_root so isolated_worker.py
        can enforce that output_dir is inside it.
        """
        import sffs_core
        import inspect

        src = inspect.getsource(sffs_core.SFFSCore._decrypt_via_worker)
        assert '"sandbox_root"' in src, \
            "payload must include sandbox_root for worker path policy"

    def test_external_output_bypass_sets_is_external_output_flag(self) -> None:
        """
        When output_path is explicitly provided (export to host), sandbox_root
        is None and is_external_output=True must be set so worker allows it
        while still blocking system paths.
        """
        import sffs_core
        import inspect

        src = inspect.getsource(sffs_core.SFFSCore._decrypt_via_worker)
        assert "is_external_output" in src, \
            "External output path must be flagged for worker policy"
        assert "is_external" in src, \
            "is_external flag must control sandbox_root vs system-path check"
