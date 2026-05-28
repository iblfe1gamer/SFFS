"""
secure_app_launcher.py — Student 2 secure external viewer launcher.

Enforces portable-app and sandbox path policy from `apps/apps_manifest.json`
before launching any external process.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import threading
import shutil
from pathlib import Path
from typing import Any

from os_isolation import detect_isolation


class LauncherPolicyError(PermissionError):
    """Raised when a launch request violates sandbox/app policy."""


def _is_within(child: Path, parent: Path) -> bool:
    child = child.resolve()
    parent = parent.resolve()
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _repo_root() -> Path:
    # code2/secure_app_launcher.py -> repo root
    return Path(__file__).resolve().parents[1]


def _safe_cleanup_temp(working_dir: Path) -> None:
    """
    Best-effort cleanup for viewer temp artifacts.

    Deletes all files/dirs under working_dir. This is intentionally scoped to the
    sandbox temp root configured by policy.
    """
    if not working_dir.exists():
        return
    for child in list(working_dir.iterdir()):
        try:
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
        except Exception:
            # Cleanup is defensive/best-effort and must never crash launch flow.
            pass


def _start_cleanup_watcher(proc: subprocess.Popen, working_dir: Path) -> None:
    """Background watcher that cleans temp artifacts after viewer exits."""
    def _watch() -> None:
        try:
            proc.wait(timeout=None)
        finally:
            _safe_cleanup_temp(working_dir)

    t = threading.Thread(target=_watch, daemon=True)
    t.start()


def _load_manifest(manifest_path: Path | None = None) -> dict[str, Any]:
    root = _repo_root()
    mpath = manifest_path or (root / "apps" / "apps_manifest.json")
    if not mpath.exists():
        raise FileNotFoundError(f"Missing apps manifest: {mpath}")
    data = json.loads(mpath.read_text(encoding="utf-8"))
    if "policy" not in data or "routes" not in data or "apps" not in data:
        raise ValueError("Invalid apps manifest: missing required keys")
    return data


def _secure_mode_enforced(policy: dict[str, Any]) -> None:
    if not bool(policy.get("secure_mode_required", False)):
        return
    status = detect_isolation()
    if status.get("active", False):
        return
    # Windows: allow launches when SFFS was not started via sffs.bat by assigning this
    # process to a Job Object here (same limits as windows_job_wrapper.py).
    if platform.system().lower() == "windows":
        from windows_job_wrapper import try_activate_job_for_current_process

        if try_activate_job_for_current_process():
            return
    if not status.get("active", False):
        raise LauncherPolicyError(
            f"Secure launch requires active OS isolation: "
            f"platform={status.get('platform')} mode={status.get('mode')} reason={status.get('reason')}. "
            f"Start with sffs.bat or ensure this process can be assigned to a Windows Job Object "
            f"(some parent shells already confine the process in an incompatible job)."
        )


def resolve_launch(
    target_file: Path,
    manifest_path: Path | None = None,
    allowed_root: Path | None = None,
) -> dict[str, Any]:
    """
    Resolve and validate launch policy without starting a process.

    Args:
        target_file: File to open.
        manifest_path: Override manifest location (tests / custom deployments).
        allowed_root: Override the manifest's allowed_open_root with an absolute
            path.  Pass ``core.sandbox["decrypted_dir"]`` so per-session sandbox
            directories (e.g. ``sandbox/sandbox_<id>/decrypted/``) are accepted
            without weakening the static manifest policy used by CLI callers.

    Returns:
        Dict with exe_path, args, working_dir, target_file, app_id.
    """
    root = _repo_root()
    manifest = _load_manifest(manifest_path)
    policy = manifest["policy"]
    routes = manifest["routes"]
    apps = manifest["apps"]

    _secure_mode_enforced(policy)

    target_file = Path(target_file).resolve()
    if allowed_root is not None:
        allowed_open_root = Path(allowed_root).resolve()
    else:
        allowed_open_root = (root / policy["allowed_open_root"]).resolve()
    if not _is_within(target_file, allowed_open_root):
        raise LauncherPolicyError(
            f"Target file must be inside sandbox open root: {allowed_open_root}"
        )
    if not target_file.exists() or not target_file.is_file():
        raise FileNotFoundError(f"Target file not found: {target_file}")

    ext = target_file.suffix.lower()
    app_id = routes.get(ext)
    if not app_id:
        raise LauncherPolicyError(f"No app mapping for extension: {ext}")
    app_def = apps.get(app_id)
    if not app_def:
        raise LauncherPolicyError(f"Mapped app '{app_id}' missing from manifest apps")

    apps_root = (root / policy["apps_root"]).resolve()
    exe_path = (root / app_def["exe_rel"]).resolve()
    if not _is_within(exe_path, apps_root):
        raise LauncherPolicyError(f"Executable path escapes apps root: {exe_path}")
    if not exe_path.exists():
        raise FileNotFoundError(f"Viewer executable not found: {exe_path}")

    working_dir = (root / policy["working_dir"]).resolve()
    working_dir.mkdir(parents=True, exist_ok=True)
    if not _is_within(working_dir, (root / "sffs_data" / "sandbox").resolve()):
        raise LauncherPolicyError("Configured working directory is outside sandbox")

    base_args = app_def.get("args", [])
    if not isinstance(base_args, list) or any(not isinstance(a, str) for a in base_args):
        raise ValueError(f"Invalid args for app '{app_id}'")

    return {
        "app_id": app_id,
        "exe_path": exe_path,
        "args": [*base_args, str(target_file)],
        "working_dir": working_dir,
        "target_file": target_file,
    }


def launch_sandbox_file(
    target_file: Path,
    *,
    wait: bool = False,
    manifest_path: Path | None = None,
    allowed_root: Path | None = None,
) -> dict[str, Any]:
    """
    Launch a sandbox file with the mapped portable app under strict policy.

    Pass ``allowed_root`` to accept per-session decrypted dirs that differ from
    the static manifest path (e.g. ``sandbox/sandbox_<id>/decrypted/``).
    """
    launch = resolve_launch(target_file, manifest_path=manifest_path, allowed_root=allowed_root)
    cmd = [str(launch["exe_path"]), *launch["args"]]
    working_dir = launch["working_dir"]
    # Proactively clear stale temporary artifacts before starting a viewer.
    _safe_cleanup_temp(working_dir)

    env = dict(os.environ)
    env["SFFS_EXTERNAL_VIEWER"] = "1"
    env["SFFS_EXTERNAL_APP_ID"] = launch["app_id"]
    # Encourage apps to keep temporary state inside sandbox temp.
    env["TEMP"] = str(working_dir)
    env["TMP"] = str(working_dir)
    env["TMPDIR"] = str(working_dir)
    env["HOME"] = str(working_dir)
    if platform.system().lower() == "windows":
        env["USERPROFILE"] = str(working_dir)

    proc = subprocess.Popen(
        cmd,
        cwd=str(working_dir),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if platform.system().lower() == "windows" else 0,
    )
    result = {
        "status": "launched",
        "app_id": launch["app_id"],
        "pid": proc.pid,
        "exe_path": str(launch["exe_path"]),
        "target_file": str(launch["target_file"]),
    }
    if wait:
        rc = proc.wait()
        _safe_cleanup_temp(working_dir)
        result["returncode"] = rc
        result["status"] = "exited"
    else:
        _start_cleanup_watcher(proc, working_dir)
    result["cleanup_policy"] = "sandbox-temp-prelaunch-and-postexit"
    return result


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Secure external launcher for sandbox files")
    ap.add_argument("file", nargs="?", help="File inside sffs_data/sandbox/decrypted")
    ap.add_argument("--resolve-only", action="store_true", help="Validate and print resolved launch")
    ap.add_argument("--wait", action="store_true", help="Wait for viewer process to exit")
    args = ap.parse_args()

    if not args.file:
        raise SystemExit("Usage: python code2/secure_app_launcher.py <sandbox-file>")

    try:
        if args.resolve_only:
            print(json.dumps(resolve_launch(Path(args.file)), indent=2, default=str))
        else:
            out = launch_sandbox_file(Path(args.file), wait=args.wait)
            print(json.dumps(out, indent=2))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}, indent=2))
        raise SystemExit(1)
