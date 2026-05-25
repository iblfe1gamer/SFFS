"""Resolve-only integration check for portable viewers (no GUI spawn)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: verify_usb_launchers.py <SFFS_ROOT>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    code2 = root / "code2"
    if not (code2 / "secure_app_launcher.py").is_file():
        print(f"Missing {code2 / 'secure_app_launcher.py'}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(code2))
    import secure_app_launcher as sal  # noqa: E402

    mpath = root / "apps" / "apps_manifest.json"
    data = json.loads(mpath.read_text(encoding="utf-8"))
    data["policy"]["secure_mode_required"] = False
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f, indent=2)
        tmp_manifest = Path(f.name)

    sal._repo_root = lambda: root

    dec = root / "sffs_data" / "sandbox" / "decrypted"
    dec.mkdir(parents=True, exist_ok=True)

    probes: list[tuple[str, str]] = [
        ("probe.txt", "notepadpp"),
        ("probe.pdf", "sumatrapdf"),
        ("probe.mp4", "vlc"),
        ("probe.docx", "libreoffice"),
        ("probe.png", "imageglass"),
        ("probe.zip", "7zip"),
    ]

    ok_n = 0
    for name, expected in probes:
        p = dec / name
        p.write_bytes(b"probe")
        try:
            out = sal.resolve_launch(p, manifest_path=tmp_manifest)
            match = out["app_id"] == expected
            if match:
                ok_n += 1
            print(
                f"{'OK' if match else 'MISMATCH'}: {name} -> {out['app_id']} "
                f"exe={out['exe_path']}"
            )
        except Exception as e:
            print(f"FAIL: {name} (expect {expected}): {type(e).__name__}: {e}")

    tmp_manifest.unlink(missing_ok=True)
    print(f"\nResolved OK: {ok_n}/{len(probes)}")
    return 0 if ok_n == len(probes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
