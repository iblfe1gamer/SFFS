"""
Read-only viewer for files decrypted into the sandbox (text or hex preview).
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QTextEdit, QVBoxLayout


def show_sandbox_file_viewer(parent, path: Path, max_bytes: int = 512_000) -> None:
    """Show UTF-8 text or a hex preview for binary files."""
    path = Path(path)
    dlg = QDialog(parent)
    dlg.setWindowTitle(f"Sandbox: {path.name}")
    dlg.resize(720, 520)
    lay = QVBoxLayout(dlg)
    lay.addWidget(QLabel(str(path)))

    te = QTextEdit()
    te.setReadOnly(True)
    data = path.read_bytes()[:max_bytes]
    try:
        te.setPlainText(data.decode("utf-8"))
    except UnicodeDecodeError:
        hx = data[:16_384].hex()
        te.setPlainText(
            "(Binary - hex preview, first 16 KiB)\n\n" + " ".join(hx[i : i + 2] for i in range(0, len(hx), 2))
        )
    if path.stat().st_size > max_bytes:
        te.append(f"\n\n... truncated (file size {path.stat().st_size} bytes)")
    lay.addWidget(te)
    dlg.exec()
