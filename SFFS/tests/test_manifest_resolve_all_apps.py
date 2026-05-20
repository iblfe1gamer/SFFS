"""Ensure apps_manifest.json paths resolve for every mapped app (no real exes)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import secure_app_launcher as sal


def _write_tree(root: Path, rel: str) -> None:
    p = root / rel.replace("/", "\\")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\x4d\x5a\x00")  # minimal stub; launcher only checks exists()


def test_resolve_launch_succeeds_for_each_manifest_app(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path
    manifest_path = Path(__file__).resolve().parents[1] / "apps" / "apps_manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["policy"]["secure_mode_required"] = False

    for app in data["apps"].values():
        _write_tree(root, app["exe_rel"])

    out_manifest = root / "apps" / "apps_manifest.json"
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    out_manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    decrypted = root / "sffs_data" / "sandbox" / "decrypted"
    temp = root / "sffs_data" / "sandbox" / "temp"
    decrypted.mkdir(parents=True, exist_ok=True)
    temp.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(sal, "_repo_root", lambda: root)

    seen: set[str] = set()
    for ext, app_id in data["routes"].items():
        if app_id in seen:
            continue
        seen.add(app_id)
        target = decrypted / f"probe{ext}"
        target.write_text("x", encoding="utf-8")
        out = sal.resolve_launch(target, manifest_path=out_manifest)
        assert out["app_id"] == app_id
        assert out["exe_path"].exists()
