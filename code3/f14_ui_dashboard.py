"""
f14_ui_dashboard.py — SFFS Student 3: Main PyQt6 shell

PyQt6 provides native widgets, drag-and-drop, and threading integration without
shipping a full browser runtime (contrast Electron). Signals/slots connect UI
controls to handlers; cross-thread updates use ``pyqtSignal`` from workers
(see ``f18_thread_controller.py``).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QApplication,
)


def apply_sffs_theme(app: QApplication) -> None:
    """Dark, high-contrast stylesheet for the whole application."""
    app.setStyleSheet(
        """
        QMainWindow, QDialog { background-color: #1a1d23; color: #e8eaed; }
        QWidget { color: #e8eaed; font-size: 13px; }
        QGroupBox {
            font-weight: 600;
            border: 1px solid #3c424c;
            border-radius: 8px;
            margin-top: 12px;
            padding: 16px 12px 12px 12px;
            background-color: #22262e;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #8ab4f8;
        }
        QPushButton {
            background-color: #2d333b;
            border: 1px solid #4a5059;
            border-radius: 6px;
            padding: 8px 16px;
            min-height: 20px;
        }
        QPushButton:hover { background-color: #3d4450; border-color: #5a6170; }
        QPushButton:pressed { background-color: #1e2228; }
        QPushButton:disabled { color: #6b7280; background-color: #252a32; }
        QListWidget {
            background-color: #16191f;
            border: 1px solid #3c424c;
            border-radius: 6px;
            padding: 4px;
        }
        QListWidget::item:selected {
            background-color: #394867;
            color: #e8eaed;
        }
        QProgressBar {
            border: 1px solid #3c424c;
            border-radius: 4px;
            text-align: center;
            background-color: #16191f;
        }
        QProgressBar::chunk { background-color: #669f66; border-radius: 3px; }
        QLineEdit {
            background-color: #16191f;
            border: 1px solid #3c424c;
            border-radius: 6px;
            padding: 8px;
            selection-background-color: #394867;
        }
        QLabel#titleLabel { color: #f28b82; font-weight: bold; }
        QLabel#hintLabel { color: #9aa0a6; font-size: 12px; }
        DragDropZone {
            border: 2px dashed #5f6368;
            border-radius: 10px;
            min-height: 140px;
            background-color: #16191f;
        }
        """
    )


class DragDropZone(QFrame):
    """Accepts file drops and emits the first local file path."""

    file_dropped = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self._label = QLabel("Drop a file here\nor click Browse")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setObjectName("hintLabel")
        self._browse = QPushButton("Browse...")
        self._browse.clicked.connect(self._browse_file)
        vl = QVBoxLayout(self)
        vl.addStretch()
        vl.addWidget(self._label)
        vl.addWidget(self._browse, alignment=Qt.AlignmentFlag.AlignCenter)
        vl.addStretch()
        self._apply_state("idle")

    def _apply_state(self, state: str) -> None:
        if state == "idle":
            self.setStyleSheet(
                "DragDropZone { border: 2px dashed #5f6368; border-radius: 10px; "
                "min-height: 140px; background-color: #16191f; }"
            )
        elif state == "hover":
            self.setStyleSheet(
                "DragDropZone { border: 2px dashed #81c995; border-radius: 10px; "
                "min-height: 140px; background-color: #1b2e1f; }"
            )
        else:  # dropped
            self.setStyleSheet(
                "DragDropZone { border: 2px solid #8ab4f8; border-radius: 10px; "
                "min-height: 140px; background-color: #1a2332; }"
            )

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose file to encrypt", "")
        if path:
            self._label.setText(Path(path).name)
            self._apply_state("drop")
            self.file_dropped.emit(path)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._apply_state("hover")
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._apply_state("idle")

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            p = urls[0].toLocalFile()
            self._label.setText(Path(p).name)
            self._apply_state("drop")
            self.file_dropped.emit(p)
        event.acceptProposedAction()


class SFSSDashboard(QMainWindow):
    """Primary window after authentication."""

    def __init__(
        self,
        session_token: str,
        config: dict,
        paths: dict,
        core=None,
        on_logout=None,
    ) -> None:
        super().__init__()
        self.setMinimumSize(920, 640)
        self.setWindowTitle("SFFS - Smart File Fortify System")
        self._session = session_token
        self._config = config
        self._paths = paths
        self._core = core
        self._on_logout = on_logout
        self._selected_file: str | None = None

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("SFFS")
        title.setObjectName("titleLabel")
        tf = QFont()
        tf.setPointSize(22)
        tf.setBold(True)
        title.setFont(tf)
        sub = QLabel("Secure file fortify")
        sub.setObjectName("hintLabel")
        hv = QVBoxLayout()
        hv.addWidget(title)
        hv.addWidget(sub)
        header.addLayout(hv)
        header.addStretch()
        user = QLabel("Signed in")
        user.setObjectName("hintLabel")
        header.addWidget(user)
        self._lock_btn = QPushButton("End session")
        self._out_btn = QPushButton("Logout")
        header.addWidget(self._lock_btn)
        header.addWidget(self._out_btn)
        outer.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(splitter, 1)

        # --- Left: operations ---
        left_wrap = QWidget()
        left = QVBoxLayout(left_wrap)
        files_gb = QGroupBox("Files")
        fv = QVBoxLayout(files_gb)
        self._drop = DragDropZone()
        fv.addWidget(self._drop)
        row = QHBoxLayout()
        self._enc = QPushButton("Encrypt selection")
        self._dec = QPushButton("Decrypt .sffs…")
        self._enc.setEnabled(False)
        self._dec.setEnabled(False)
        row.addWidget(self._enc)
        row.addWidget(self._dec)
        fv.addLayout(row)
        self._bar = QProgressBar()
        self._bar.setVisible(False)
        self._bar.setMaximum(100)
        fv.addWidget(self._bar)
        self._status = QLabel("Ready — select a file above")
        self._status.setObjectName("hintLabel")
        self._status.setWordWrap(True)
        fv.addWidget(self._status)
        left.addWidget(files_gb)

        if core is not None:
            hint = QLabel(
                "AES file keys mix OS randomness with your mouse movement. "
                "Your login password unlocks the RSA keystore for this session only."
            )
            hint.setObjectName("hintLabel")
            hint.setWordWrap(True)
            left.addWidget(hint)

            sb_gb = QGroupBox("Sandbox (decrypted copies)")
            sv = QVBoxLayout(sb_gb)
            self._sandbox_list = QListWidget()
            self._sandbox_list.setMinimumHeight(160)
            self._sandbox_list.setAlternatingRowColors(True)
            sv.addWidget(self._sandbox_list)
            br = QHBoxLayout()
            btn_sffs = QPushButton("Open .sffs in viewer…")
            btn_ref = QPushButton("Refresh")
            br.addWidget(btn_sffs)
            br.addWidget(btn_ref)
            sv.addLayout(br)
            left.addWidget(sb_gb)
            btn_ref.clicked.connect(self.refresh_sandbox_list)
            btn_sffs.clicked.connect(self._pick_sffs_to_view)
            self._sandbox_list.itemDoubleClicked.connect(self._open_sandbox_item)

        left.addStretch()
        splitter.addWidget(left_wrap)

        # --- Right: status ---
        right_wrap = QWidget()
        right = QVBoxLayout(right_wrap)
        sec_gb = QGroupBox("Security status")
        svl = QVBoxLayout(sec_gb)
        self._sec = QLabel("All clear")
        self._sec.setStyleSheet("color: #81c995; font-weight: 600;")
        svl.addWidget(self._sec)
        self._logs = QLabel("Session logs appear in the audit database on your USB.")
        self._logs.setObjectName("hintLabel")
        self._logs.setWordWrap(True)
        svl.addWidget(self._logs)
        cloud = QPushButton("Cloud backup (optional)")
        svl.addWidget(cloud)
        if core is not None:
            cloud.setEnabled(True)
            cloud.clicked.connect(self._on_cloud_backup)
        else:
            cloud.setEnabled(False)
            cloud.setToolTip("Enable Google Drive in config when available")
        right.addWidget(sec_gb)

        free = paths.get("free_space_gb", "?")
        meta = QLabel(f"USB free space: ~{free} GB  ·  SFFS v1.0")
        meta.setObjectName("hintLabel")
        right.addWidget(meta)
        right.addStretch()
        splitter.addWidget(right_wrap)
        splitter.setSizes([520, 380])

        self._drop.file_dropped.connect(self.setEncryptMode)

        if on_logout:
            self._out_btn.clicked.connect(on_logout)
            self._lock_btn.clicked.connect(on_logout)

    def refresh_sandbox_list(self) -> None:
        if not self._core or not hasattr(self, "_sandbox_list"):
            return
        self._sandbox_list.clear()
        for p in self._core.list_sandbox_files():
            self._sandbox_list.addItem(str(p))

    def _open_sandbox_item(self, item: QListWidgetItem) -> None:
        from sandbox_viewer import show_sandbox_file_viewer

        mode = show_sandbox_file_viewer(self, Path(item.text()))
        if mode == "external":
            self._status.setText(f"Opened with secure external viewer: {Path(item.text()).name}")
        elif mode == "inline":
            self._status.setText(f"Opened inline preview: {Path(item.text()).name}")

    def _pick_sffs_to_view(self) -> None:
        if not self._core:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose .sffs", "", "SFFS (*.sffs)"
        )
        if not path:
            return
        from sandbox_viewer import show_sandbox_file_viewer

        try:
            out = self._core.ensure_decrypted_for_view(Path(path))
            mode = show_sandbox_file_viewer(self, out)
            self.refresh_sandbox_list()
            if mode == "external":
                self._status.setText(f"Opened with secure external viewer: {out.name}")
            elif mode == "inline":
                self._status.setText(f"Opened inline preview: {out.name}")
        except Exception as e:
            QMessageBox.warning(self, "View failed", str(e))

    def updateProgress(self, percent: int) -> None:
        self._bar.setVisible(True)
        self._bar.setValue(percent)

    def showSecurityAlert(self, message: str, severity: str) -> None:
        color = "#f28b82" if severity.upper() == "CRITICAL" else "#fdd663"
        self._sec.setStyleSheet(f"color: {color}; font-weight: 600;")
        self._sec.setText(message)

    def setEncryptMode(self, file_path: str) -> None:
        self._selected_file = file_path
        self._enc.setEnabled(True)
        self._dec.setEnabled(True)
        self._status.setText(f"Selected: {Path(file_path).name}")

    def _on_cloud_backup(self) -> None:
        """Trigger cloud backup of keys via sffs_core.backupKeys()."""
        if self._core is None:
            return
        result = self._core.backupKeys()
        status = result.get("status", "unknown")
        if status == "not_authenticated":
            reply = QMessageBox.question(
                self, "Connect to Google Drive",
                "Back up your encrypted keys to Google Drive.\n\n"
                "Your browser will open for a one-time Google sign-in.\n"
                "Do you want to connect now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._run_google_auth()
        elif status in ("offline", "no_keys", "skipped"):
            QMessageBox.information(self, "Cloud Backup", result.get("message", status))
        else:
            QMessageBox.information(self, "Cloud Backup", f"Backup complete:\n{result}")

    def _run_google_auth(self) -> None:
        from PyQt6.QtCore import QThread, pyqtSignal, Qt
        from PyQt6.QtWidgets import QProgressDialog

        config_dir = self._core.paths["config_dir"]

        class _AuthWorker(QThread):
            finished = pyqtSignal(bool, str)

            def __init__(self, cfg):
                super().__init__()
                self._cfg = cfg

            def run(self):
                try:
                    from f16_cloud_sync import authenticateGoogleDrive
                    authenticateGoogleDrive(self._cfg)  # uses bundled secret
                    self.finished.emit(True, "")
                except Exception as exc:
                    self.finished.emit(False, str(exc))

        self._auth_worker = _AuthWorker(config_dir)
        dlg = QProgressDialog(
            "Your browser is opening for Google sign-in.\n"
            "Complete the sign-in, then return here.",
            "Cancel", 0, 0, self,
        )
        dlg.setWindowTitle("Connect to Google Drive")
        dlg.setWindowModality(Qt.WindowModality.WindowModal)
        dlg.canceled.connect(self._auth_worker.terminate)
        self._auth_dlg = dlg

        def _on_done(ok, err):
            dlg.close()
            if ok:
                res = self._core.backupKeys()
                QMessageBox.information(self, "Cloud Backup", f"Backup complete:\n{res}")
            else:
                QMessageBox.critical(
                    self, "Connection Failed",
                    f"Could not connect to Google Drive:\n{err}",
                )

        self._auth_worker.finished.connect(_on_done)
        self._auth_worker.start()
        dlg.exec()

    def refreshLogs(self, log_entries: list) -> None:
        lines = "\n".join(str(e) for e in log_entries[-5:])
        self._logs.setText(lines or "No log lines")


def uiDashboard(session_token: str, config: dict, paths: dict) -> None:
    """
    Start (or reuse) ``QApplication`` and show the main dashboard.

    Args:
        session_token: Active session id string.
        config: Loaded configuration dict.
        paths: Path map from ``initDriveDetection()``.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    apply_sffs_theme(app)
    win = SFSSDashboard(session_token, config, paths)
    win.show()
    app.exec()


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        apply_sffs_theme(app)
    except Exception as e:
        print("Headless / no display:", e)
        sys.exit(0)
    paths = {
        "data_dir": Path.cwd() / "sffs_data",
        "free_space_gb": 0.0,
    }
    paths["data_dir"].mkdir(parents=True, exist_ok=True)
    win = SFSSDashboard("demo-session-token", {}, paths)
    win.show()
    app.exec()
