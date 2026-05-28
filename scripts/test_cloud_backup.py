"""
Standalone cloud backup test.
Run from repo root: python scripts/test_cloud_backup.py

Steps:
  1. OAuth (opens browser once — token saved after)
  2. Upload a test file
  3. List to verify
  4. Delete the test file
  5. List again to confirm deletion
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_CODE3 = _ROOT / "code3"
for p in (_CODE3, _ROOT / "main-code"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from f16_cloud_sync import authenticateGoogleDrive, cloudSync, loadCredentials

CFG_DIR = _ROOT / "sffs_data" / "config"
CFG_DIR.mkdir(parents=True, exist_ok=True)


def step(label: str) -> None:
    print(f"\n{'-'*50}")
    print(f"  {label}")
    print(f"{'-'*50}")


def main() -> None:
    # ── 1. Auth ──────────────────────────────────────────
    step("1 / 5  Auth check")
    creds = loadCredentials(CFG_DIR)
    if creds and creds.valid:
        print("  Token already valid — skipping OAuth.")
    else:
        print("  No valid token found.")
        print("  Browser will open for Google sign-in ...")
        try:
            authenticateGoogleDrive(CFG_DIR)
            print("  Auth OK — token saved to", CFG_DIR / "google_token.json")
        except Exception as e:
            print(f"  AUTH FAILED: {e}")
            sys.exit(1)

    # ── 2. Upload ────────────────────────────────────────
    step("2 / 5  Upload test file")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir=CFG_DIR
    ) as f:
        tmp = Path(f.name)
        json.dump({"test": True, "source": "test_cloud_backup.py"}, f)

    print(f"  Uploading: {tmp.name}")
    up = cloudSync("upload", local_path=tmp, config_dir=CFG_DIR)
    print(f"  Result: {up}")

    if up.get("status") != "uploaded":
        print("  UPLOAD FAILED — aborting.")
        tmp.unlink(missing_ok=True)
        sys.exit(1)

    file_id = up["file_id"]
    drive_path = up.get("drive_path")
    print(f"  file_id  : {file_id}")
    print(f"  drive_path: {drive_path}")
    tmp.unlink(missing_ok=True)

    # ── 3. List ──────────────────────────────────────────
    step("3 / 5  List backup folder")
    lst = cloudSync("list", config_dir=CFG_DIR)
    print(f"  Status: {lst.get('status')}")
    files = lst.get("files", [])
    print(f"  Files in SFFS_Backup ({len(files)}):")
    for f in files:
        marker = " ← just uploaded" if f["file_id"] == file_id else ""
        print(f"    {f['name']}  id={f['file_id']}  size={f.get('size')}B{marker}")

    found = any(f["file_id"] == file_id for f in files)
    print(f"  Uploaded file found in listing: {'YES ✓' if found else 'NO ✗'}")

    # ── 4. Delete ────────────────────────────────────────
    step("4 / 5  Delete test file")
    dl = cloudSync("delete", file_id=file_id, config_dir=CFG_DIR)
    print(f"  Result: {dl}")
    if dl.get("status") != "deleted":
        print("  DELETE FAILED.")
        sys.exit(1)
    print("  Deleted OK ✓")

    # ── 5. Confirm gone ──────────────────────────────────
    step("5 / 5  Verify deletion")
    lst2 = cloudSync("list", config_dir=CFG_DIR)
    files2 = lst2.get("files", [])
    still_there = any(f["file_id"] == file_id for f in files2)
    still_msg = "YES - DELETE DID NOT WORK" if still_there else "NO - confirmed deleted"
    print(f"  File still present: {still_msg}")
    print(f"\n  Remaining files in SFFS_Backup: {len(files2)}")

    # -- Summary --
    print(f"\n{'='*50}")
    all_pass = (
        up.get("status") == "uploaded"
        and found
        and dl.get("status") == "deleted"
        and not still_there
    )
    print(f"  OVERALL: {'PASS' if all_pass else 'FAIL'}")
    print(f"{'='*50}\n")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
