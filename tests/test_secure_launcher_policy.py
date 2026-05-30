"""Policy tests for secure external viewer launcher."""

import json
from pathlib import Path

import pytest

import secure_app_launcher as sal
from secure_app_launcher import LauncherPolicyError
from sffs_core import SFFSCore


def _write_manifest(
    root: Path,
    exe_rel: str = "apps/notepadpp/notepad++.exe",
    *,
    create_exe: bool = True,
) -> Path:
    apps_dir = root / "apps" / "notepadpp"
    apps_dir.mkdir(parents=True, exist_ok=True)
    if create_exe:
        (root / exe_rel).write_text("fake-exe", encoding="utf-8")

    decrypted = root / "sffs_data" / "sandbox" / "decrypted"
    temp = root / "sffs_data" / "sandbox" / "temp"
    decrypted.mkdir(parents=True, exist_ok=True)
    temp.mkdir(parents=True, exist_ok=True)

    manifest = {
        "manifest_version": "1.0",
        "policy": {
            "apps_root": "apps",
            "allowed_open_root": "sffs_data/sandbox/decrypted",
            "working_dir": "sffs_data/sandbox/temp",
            "secure_mode_required": False,
        },
        "routes": {".txt": "notepadpp"},
        "apps": {"notepadpp": {"exe_rel": exe_rel, "args": []}},
    }
    mpath = root / "apps" / "apps_manifest.json"
    mpath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return mpath


def test_resolve_launch_allows_mapped_file_inside_sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mpath = _write_manifest(tmp_path)
    target = tmp_path / "sffs_data" / "sandbox" / "decrypted" / "ok.txt"
    target.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)

    out = sal.resolve_launch(target, manifest_path=mpath)
    assert out["app_id"] == "notepadpp"
    assert out["target_file"] == target.resolve()
    assert str(out["exe_path"]).endswith("apps\\notepadpp\\notepad++.exe") or str(out["exe_path"]).endswith(
        "apps/notepadpp/notepad++.exe"
    )


def test_resolve_launch_blocks_path_escape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mpath = _write_manifest(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("nope", encoding="utf-8")
    monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)

    with pytest.raises(LauncherPolicyError):
        sal.resolve_launch(outside, manifest_path=mpath)


def test_resolve_launch_fails_when_mapped_app_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mpath = _write_manifest(tmp_path, exe_rel="apps/notepadpp/missing.exe", create_exe=False)
    target = tmp_path / "sffs_data" / "sandbox" / "decrypted" / "ok.txt"
    target.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(sal, "_repo_root", lambda: tmp_path)

    with pytest.raises(FileNotFoundError):
        sal.resolve_launch(target, manifest_path=mpath)


def test_core_terminate_active_viewers_invokes_taskkill(monkeypatch: pytest.MonkeyPatch) -> None:
    core = SFFSCore()
    core.register_external_viewer_pid(1111)
    core.register_external_viewer_pid(2222)

    calls: list[list[str]] = []

    class DummyProc:
        def wait(self, timeout=None):
            return 0

    def fake_popen(cmd, stdout=None, stderr=None, **kwargs):
        calls.append(cmd)
        return DummyProc()

    monkeypatch.setattr("sffs_core.subprocess.Popen", fake_popen)
    core._terminate_active_viewers()

    assert any("/PID" in cmd and "1111" in cmd for cmd in calls)
    assert any("/PID" in cmd and "2222" in cmd for cmd in calls)
