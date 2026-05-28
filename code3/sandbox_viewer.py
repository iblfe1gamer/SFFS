"""
Read-only viewer for files decrypted into the sandbox.

Text-like files are previewed inline. Binary/media/document files are opened
through the secure portable-app launcher so files stay inside SFFS policy.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QDialog, QLabel, QMessageBox, QTextEdit, QVBoxLayout

_TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".csv",
    ".log",
    ".xml",
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".sql",
}


def _decode_text_preview(data: bytes) -> str | None:
    """Try decoding as common text encodings with a simple readability gate."""
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            text = data.decode(enc)
        except UnicodeDecodeError:
            continue
        if not text:
            continue
        printable = sum(ch.isprintable() or ch in "\r\n\t" for ch in text)
        ratio = printable / len(text)
        if ratio >= 0.9:
            return text
    return None


def _audit(parent, event: str, severity: str, metadata: dict | None = None) -> None:
    """Best-effort audit log hook through active core logger."""
    core = getattr(parent, "_core", None)
    logger = getattr(core, "logger", None) if core is not None else None
    if logger is None:
        return
    try:
        logger.log(
            event,
            severity,
            module="sandbox_viewer",
            user_id=getattr(core, "_user_id", None),
            metadata=metadata or {},
        )
    except Exception:
        pass


def _launch_with_policy(parent, path: Path) -> bool:
    """Launch non-text files via secure app policy in code2."""
    try:
        from secure_app_launcher import launch_sandbox_file
    except Exception:
        # Keep code3 standalone demos working by injecting code2 path on demand.
        code2_root = Path(__file__).resolve().parent.parent / "code2"
        if str(code2_root) not in sys.path:
            sys.path.insert(0, str(code2_root))
        from secure_app_launcher import launch_sandbox_file  # type: ignore

    core = getattr(parent, "_core", None)
    # Pass the session's actual decrypted_dir so per-session sandbox paths
    # (sandbox/sandbox_<id>/decrypted/) pass the launcher policy check.
    allowed_root = None
    if core is not None:
        sb = getattr(core, "sandbox", None) or {}
        _dec = sb.get("decrypted_dir")
        if _dec:
            allowed_root = Path(_dec)

    # Pre-launch integrity gate: verify file is in the decrypted registry and
    # its hash still matches what was stored at decrypt time.
    if core is not None and hasattr(core, "validate_before_open"):
        try:
            core.validate_before_open(path)
        except Exception as voe:
            _audit(
                parent,
                "Pre-launch validation failed",
                "ERROR",
                {"path": str(path), "reason": str(voe)},
            )
            QMessageBox.critical(
                parent,
                "Open Blocked",
                f"Pre-launch integrity check failed:\n{voe}",
            )
            return False

    try:
        res = launch_sandbox_file(path, wait=False, allowed_root=allowed_root)
        if core is not None and hasattr(core, "register_external_viewer_pid"):
            try:
                core.register_external_viewer_pid(int(res.get("pid")))
            except Exception:
                pass
        _audit(
            parent,
            "External viewer launched",
            "INFO",
            {"path": str(path), "app_id": res.get("app_id"), "pid": res.get("pid")},
        )
        return True
    except Exception as e:
        _audit(
            parent,
            "External viewer blocked",
            "WARN",
            {"path": str(path), "error": str(e)},
        )
        QMessageBox.warning(
            parent,
            "Open blocked",
            f"Could not open file under secure app policy:\n{path}\n\n{e}",
        )
        return False


def show_sandbox_file_viewer(parent, path: Path, max_bytes: int = 512_000) -> str:
    """Show text preview inline, or launch secure external viewer for non-text.

    Returns:
        "inline" when shown in app, "external" when launched externally,
        "error" when opening failed.
    """
    path = Path(path).resolve()

    # SECURITY: Validate the requested path is inside the sandbox decrypted root
    # before performing any file I/O.  Without this check, a caller could pass
    # an arbitrary host path and read any file the process can access.
    core = getattr(parent, "_core", None)
    if core is not None:
        sandbox = getattr(core, "sandbox", None)
        if sandbox:
            decrypted_root = Path(sandbox["decrypted_dir"]).resolve()
            try:
                path.relative_to(decrypted_root)
            except ValueError:
                _audit(
                    parent,
                    "Sandbox boundary violation blocked",
                    "WARN",
                    {"path": str(path), "sandbox_root": str(decrypted_root)},
                )
                QMessageBox.warning(
                    parent,
                    "Access blocked",
                    f"File is outside the sandbox boundary:\n{path}\n\n"
                    f"Only files inside the decrypted sandbox may be viewed.",
                )
                return "error"

    if not path.exists():
        QMessageBox.warning(parent, "File missing", f"Sandbox file not found:\n{path}")
        return "error"

    data = path.read_bytes()[:max_bytes]
    looks_text = path.suffix.lower() in _TEXT_SUFFIXES
    decoded = _decode_text_preview(data) if looks_text or data else None

    if decoded is None and data:
        return "external" if _launch_with_policy(parent, path) else "error"

    dlg = QDialog(parent)
    dlg.setWindowTitle(f"Sandbox: {path.name}")
    dlg.resize(720, 520)
    lay = QVBoxLayout(dlg)
    lay.addWidget(QLabel(str(path)))

    te = QTextEdit()
    te.setReadOnly(True)
    te.setPlainText(decoded or "")
    if path.stat().st_size > max_bytes:
        te.append(f"\n\n... truncated (file size {path.stat().st_size} bytes)")
    lay.addWidget(te)
    dlg.exec()
    _audit(parent, "Inline sandbox preview", "INFO", {"path": str(path)})
    return "inline"
