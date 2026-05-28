"""
sffs_ui.py — SFFS Modern UI (v2)

Completely redesigned shell for SFFS.
Design goals:
  - Modern dark "vault" aesthetic — deep navy surfaces, teal/cyan accents
  - Security feels tangible — live isolation badge, entropy meter, audit feed
  - User-friendly — sidebar nav, card layout, large hit targets, clear feedback
  - Separate from f14_ui_dashboard.py; same SFFSCore backend

Entry points:
  run_modern_ui(core, paths, config, username)   — called by main.py after login
  python sffs_ui.py                              — standalone demo
"""

from __future__ import annotations

import sys
from pathlib import Path
import platform

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QSize, pyqtSignal, QThread, pyqtSlot,
)
from PyQt6.QtGui import (
    QColor, QDragEnterEvent, QDropEvent,
    QFont, QFontDatabase, QPainter, QPalette,
    QLinearGradient, QBrush, QIcon,
)
from PyQt6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFormLayout,
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSplitter, QStackedWidget,
    QTextEdit, QVBoxLayout, QWidget, QGridLayout,
)

# ── Palette ────────────────────────────────────────────────────────────────
_BG          = "#0d1117"   # deepest background
_SURFACE     = "#161b22"   # card / panel
_SURFACE2    = "#21262d"   # elevated surface / hover
_BORDER      = "#30363d"   # default border
_BORDER_ACT  = "#388bfd"   # focused / active border
_TEXT        = "#e6edf3"   # primary text
_TEXT2       = "#8b949e"   # secondary / hint text
_ACCENT      = "#388bfd"   # primary action — blue
_SECURE      = "#3fb950"   # secure / success — green
_WARN        = "#d29922"   # warning — amber
_DANGER      = "#f85149"   # danger — red
_CRYPTO      = "#a371f7"   # encryption indicator — purple
_TEAL        = "#39c5cf"   # sandbox / viewer — teal

# ── Global stylesheet ──────────────────────────────────────────────────────
STYLESHEET = f"""
/* ── Root ── */
QMainWindow, QDialog, QWidget {{
    background-color: {_BG};
    color: {_TEXT};
    font-family: 'Segoe UI', 'SF Pro Display', 'Inter', sans-serif;
    font-size: 13px;
}}

/* ── Scroll areas ── */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: {_SURFACE};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {_BORDER};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {_TEXT2}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ── Buttons ── */
QPushButton {{
    background-color: {_SURFACE2};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 9px 20px;
    min-height: 22px;
    font-weight: 500;
    color: {_TEXT};
}}
QPushButton:hover {{
    background-color: #2d333b;
    border-color: #484f58;
}}
QPushButton:pressed {{
    background-color: {_SURFACE};
    border-color: {_BORDER_ACT};
}}
QPushButton:disabled {{
    color: #484f58;
    background-color: {_SURFACE};
    border-color: {_BORDER};
}}
QPushButton#primaryBtn {{
    background-color: {_ACCENT};
    border-color: {_ACCENT};
    color: #ffffff;
    font-weight: 600;
}}
QPushButton#primaryBtn:hover {{
    background-color: #58a6ff;
    border-color: #58a6ff;
}}
QPushButton#primaryBtn:disabled {{
    background-color: #1c2d45;
    border-color: #1c2d45;
    color: #3a5068;
}}
QPushButton#dangerBtn {{
    background-color: transparent;
    border: 1px solid {_DANGER};
    color: {_DANGER};
}}
QPushButton#dangerBtn:hover {{
    background-color: #3d1210;
}}
QPushButton#sidebarBtn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    text-align: left;
    padding: 10px 14px;
    font-size: 13px;
    font-weight: 500;
    color: {_TEXT2};
}}
QPushButton#sidebarBtn:hover {{
    background: {_SURFACE2};
    color: {_TEXT};
}}
QPushButton#sidebarBtn[active="true"] {{
    background: #1c2d45;
    color: {_ACCENT};
    border-left: 3px solid {_ACCENT};
    padding-left: 11px;
}}

/* ── Inputs ── */
QLineEdit {{
    background-color: {_SURFACE2};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    color: {_TEXT};
    font-size: 13px;
    selection-background-color: #1c2d45;
}}
QLineEdit:focus {{
    border-color: {_BORDER_ACT};
    background-color: #1c2330;
}}
QLineEdit::placeholder {{
    color: {_TEXT2};
}}

/* ── Lists ── */
QListWidget {{
    background-color: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    outline: none;
    padding: 4px;
}}
QListWidget::item {{
    padding: 8px 12px;
    border-radius: 6px;
    color: {_TEXT};
}}
QListWidget::item:hover {{ background: {_SURFACE2}; }}
QListWidget::item:selected {{
    background: #1c2d45;
    color: {_TEXT};
}}

/* ── Progress ── */
QProgressBar {{
    border: 1px solid {_BORDER};
    border-radius: 5px;
    background-color: {_SURFACE2};
    text-align: center;
    font-size: 11px;
    color: {_TEXT2};
    max-height: 8px;
}}
QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {_ACCENT}, stop:1 {_TEAL}
    );
    border-radius: 4px;
}}
QProgressBar#entropyBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {_CRYPTO}, stop:1 {_ACCENT}
    );
}}
QProgressBar#entropyBar[ready="true"]::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {_SECURE}, stop:1 {_TEAL}
    );
}}

/* ── Text edit (log view) ── */
QTextEdit {{
    background-color: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 10px;
    color: {_TEXT2};
    font-family: 'Cascadia Code', 'Consolas', 'Fira Code', monospace;
    font-size: 11px;
    selection-background-color: #1c2d45;
}}
"""


# ── Utility widgets ────────────────────────────────────────────────────────

def _shadow(radius: int = 16, alpha: int = 80) -> QGraphicsDropShadowEffect:
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(radius)
    fx.setOffset(0, 4)
    fx.setColor(QColor(0, 0, 0, alpha))
    return fx


class Card(QFrame):
    """Elevated surface card with optional title bar."""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(
            f"QFrame#card {{ background: {_SURFACE}; border: 1px solid {_BORDER}; "
            f"border-radius: 12px; }}"
        )
        self.setGraphicsEffect(_shadow())
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 20)
        self._layout.setSpacing(12)
        if title:
            lbl = QLabel(title)
            lbl.setFont(_semibold(12))
            lbl.setStyleSheet(f"color: {_TEXT2}; letter-spacing: 0.5px; text-transform: uppercase; border: none; background: transparent;")
            self._layout.addWidget(lbl)

    @property
    def body(self) -> QVBoxLayout:
        return self._layout


class Badge(QLabel):
    """Coloured pill badge for status indicators."""

    COLORS = {
        "secure":  (_SECURE,  "#0d2318"),
        "warn":    (_WARN,    "#2d1d02"),
        "danger":  (_DANGER,  "#2d0c0a"),
        "info":    (_ACCENT,  "#0c1d2d"),
        "neutral": (_TEXT2,   _SURFACE2),
        "crypto":  (_CRYPTO,  "#1a0d30"),
    }

    def __init__(self, text: str, kind: str = "neutral", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.set_kind(kind)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_kind(self, kind: str) -> None:
        fg, bg = self.COLORS.get(kind, self.COLORS["neutral"])
        self.setStyleSheet(
            f"QLabel {{ color: {fg}; background: {bg}; border: 1px solid {fg}40; "
            f"border-radius: 10px; padding: 2px 10px; font-size: 11px; font-weight: 600; }}"
        )

    def set_text_kind(self, text: str, kind: str) -> None:
        self.setText(text)
        self.set_kind(kind)


def _semibold(size: int = 13) -> QFont:
    f = QFont()
    f.setPointSize(size)
    f.setWeight(QFont.Weight.DemiBold)
    return f


def _bold(size: int = 13) -> QFont:
    f = QFont()
    f.setPointSize(size)
    f.setBold(True)
    return f


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {_BORDER}; border: none;")


# ── Drag-and-drop zone ─────────────────────────────────────────────────────

class DropZone(QFrame):
    file_dropped = pyqtSignal(str)

    _IDLE   = f"border: 2px dashed {_BORDER}; border-radius: 12px; background: {_SURFACE2};"
    _HOVER  = f"border: 2px dashed {_TEAL};   border-radius: 12px; background: #0d2028;"
    _ACTIVE = f"border: 2px solid  {_ACCENT}; border-radius: 12px; background: #0c1d2d;"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self._style("idle")

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon = QLabel("⬆")
        self._icon.setFont(_bold(28))
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setStyleSheet(f"color: {_TEXT2}; background: transparent; border: none;")

        self._hint = QLabel("Drop a file here  or")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint.setStyleSheet(f"color: {_TEXT2}; background: transparent; border: none; font-size: 13px;")

        self._browse = QPushButton("Browse…")
        self._browse.setFixedWidth(110)
        self._browse.clicked.connect(self._on_browse)

        root.addWidget(self._icon)
        root.addSpacing(4)
        root.addWidget(self._hint)
        root.addSpacing(8)
        root.addWidget(self._browse, alignment=Qt.AlignmentFlag.AlignCenter)

    def _style(self, state: str) -> None:
        styles = {"idle": self._IDLE, "hover": self._HOVER, "active": self._ACTIVE}
        self.setStyleSheet(f"QFrame {{ {styles.get(state, self._IDLE)} }}")

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select file")
        if path:
            self._set_file(path)

    def _set_file(self, path: str) -> None:
        name = Path(path).name
        self._icon.setText("📄")
        self._hint.setText(name)
        self._hint.setStyleSheet(f"color: {_TEXT}; background: transparent; border: none; font-size: 13px; font-weight: 500;")
        self._style("active")
        self.file_dropped.emit(path)

    def reset(self) -> None:
        self._icon.setText("⬆")
        self._icon.setStyleSheet(f"color: {_TEXT2}; background: transparent; border: none;")
        self._hint.setText("Drop a file here  or")
        self._hint.setStyleSheet(f"color: {_TEXT2}; background: transparent; border: none; font-size: 13px;")
        self._style("idle")

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._style("hover")

    def dragLeaveEvent(self, e) -> None:
        self._style("idle")

    def dropEvent(self, e: QDropEvent) -> None:
        urls = e.mimeData().urls()
        if urls:
            self._set_file(urls[0].toLocalFile())
        e.acceptProposedAction()


# ── Sidebar ────────────────────────────────────────────────────────────────

class SidebarButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(f"  {icon}  {label}", parent)
        self.setObjectName("sidebarBtn")
        self.setCheckable(False)
        self._active = False
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_active(self, active: bool) -> None:
        self._active = active
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QFrame):
    page_changed = pyqtSignal(int)

    PAGES = [
        ("🗂", "Files"),
        ("🔒", "Vault"),
        ("🛡", "Security"),
        ("⚙", "Settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setStyleSheet(
            f"QFrame {{ background: {_SURFACE}; border-right: 1px solid {_BORDER}; border-radius: 0; }}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 20, 12, 20)
        lay.setSpacing(4)

        # Logo block
        logo = QLabel("🔐 SFFS")
        logo.setFont(_bold(15))
        logo.setStyleSheet(f"color: {_TEXT}; padding: 0 4px 16px 4px; border: none; background: transparent;")
        lay.addWidget(logo)

        lay.addWidget(Divider())
        lay.addSpacing(8)

        self._btns: list[SidebarButton] = []
        for i, (ico, lbl) in enumerate(self.PAGES):
            btn = SidebarButton(ico, lbl)
            idx = i
            btn.clicked.connect(lambda _, n=idx: self._select(n))
            self._btns.append(btn)
            lay.addWidget(btn)

        lay.addStretch()

        # Version tag
        ver = QLabel("v2.0  ·  SFFS")
        ver.setStyleSheet(f"color: {_TEXT2}; font-size: 10px; padding: 4px; border: none; background: transparent;")
        lay.addWidget(ver)

        self._select(0)

    def _select(self, idx: int) -> None:
        for i, btn in enumerate(self._btns):
            btn.set_active(i == idx)
        self.page_changed.emit(idx)


# ── Top bar ────────────────────────────────────────────────────────────────

class TopBar(QFrame):
    end_session = pyqtSignal()

    def __init__(self, username: str = "user", parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setStyleSheet(
            f"QFrame {{ background: {_SURFACE}; border-bottom: 1px solid {_BORDER}; border-radius: 0; }}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 16, 0)

        self._page_title = QLabel("Files")
        self._page_title.setFont(_semibold(14))
        self._page_title.setStyleSheet(f"color: {_TEXT}; border: none; background: transparent;")
        lay.addWidget(self._page_title)

        lay.addStretch()

        # Security status badge
        self._sec_badge = Badge("● CHECKING", "neutral")
        lay.addWidget(self._sec_badge)

        lay.addSpacing(16)

        # User chip
        user_chip = QLabel(f"  👤 {username}  ")
        user_chip.setStyleSheet(
            f"color: {_TEXT2}; background: {_SURFACE2}; border: 1px solid {_BORDER}; "
            f"border-radius: 14px; padding: 4px 10px; font-size: 12px;"
        )
        lay.addWidget(user_chip)

        lay.addSpacing(8)

        end_btn = QPushButton("End session")
        end_btn.setObjectName("dangerBtn")
        end_btn.setFixedHeight(32)
        end_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        end_btn.clicked.connect(self.end_session)
        lay.addWidget(end_btn)

    def set_page(self, title: str) -> None:
        self._page_title.setText(title)

    def set_security(self, text: str, kind: str) -> None:
        self._sec_badge.set_text_kind(text, kind)


# ── Entropy collector (VeraCrypt-style) ────────────────────────────────────

class _EntropyCanvas(QWidget):
    """Canvas widget — mouse movement draws colored pixels and feeds entropy pool."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(440, 180)
        self.setMouseTracking(True)
        self._dots: list[tuple[int, int, QColor]] = []

    def mouseMoveEvent(self, e) -> None:  # type: ignore[override]
        try:
            from mouse_entropy import feed_mouse_entropy
            feed_mouse_entropy(e.pos().x(), e.pos().y())
        except Exception:
            pass
        import random as _rnd
        c = QColor(
            _rnd.randint(80, 255),
            _rnd.randint(80, 255),
            _rnd.randint(80, 255),
        )
        self._dots.append((e.pos().x(), e.pos().y(), c))
        self.update()
        super().mouseMoveEvent(e)

    def paintEvent(self, _e) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(_SURFACE))
        p.setPen(Qt.PenStyle.NoPen)
        for x, y, c in self._dots:
            p.setBrush(QBrush(c))
            p.drawEllipse(x - 4, y - 4, 8, 8)
        # Cross-hair hint when empty
        if not self._dots:
            p.setPen(QColor(_TEXT2))
            cx, cy = self.width() // 2, self.height() // 2
            p.drawLine(cx - 20, cy, cx + 20, cy)
            p.drawLine(cx, cy - 20, cx, cy + 20)
        p.end()


class EntropyCollectorDialog(QDialog):
    """
    VeraCrypt-style entropy collection dialog.

    Shows a canvas where mouse movement draws colored pixels.
    The Proceed button becomes active only after the entropy pool is ready
    (>= 256 bytes of mouse data accumulated in mouse_entropy.py).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Collecting Encryption Entropy")
        self.setModal(True)
        self.setFixedSize(520, 400)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 28, 28, 24)
        lay.setSpacing(14)

        # Header
        title = QLabel("🎲  Generate Encryption Entropy")
        title.setFont(_bold(14))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {_TEXT}; border: none; background: transparent;")
        lay.addWidget(title)

        info = QLabel(
            "Move your mouse randomly across the canvas below.\n"
            "Your movements seed the cryptographic randomness used to derive the file encryption key."
        )
        info.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; border: none; background: transparent;")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(info)

        # Canvas
        self._canvas = _EntropyCanvas()
        self._canvas.setStyleSheet(
            f"border: 1px solid {_BORDER}; border-radius: 8px; background: {_SURFACE};"
        )
        lay.addWidget(self._canvas, 1)

        # Progress row
        prog_row = QHBoxLayout()
        prog_row.setSpacing(8)
        self._prog = QProgressBar()
        self._prog.setMaximum(100)
        self._prog.setValue(0)
        self._prog.setFixedHeight(12)
        self._prog.setStyleSheet(
            f"QProgressBar {{ background: {_SURFACE2}; border: 1px solid {_BORDER}; "
            f"border-radius: 5px; }}"
            f"QProgressBar::chunk {{ background: {_CRYPTO}; border-radius: 5px; }}"
        )
        prog_row.addWidget(self._prog)
        self._pct_lbl = QLabel("0 %")
        self._pct_lbl.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; border: none; background: transparent;")
        self._pct_lbl.setFixedWidth(42)
        prog_row.addWidget(self._pct_lbl)
        lay.addLayout(prog_row)

        self._hint = QLabel("Move your mouse across the canvas above…")
        self._hint.setStyleSheet(f"color: {_TEXT2}; font-size: 11px; border: none; background: transparent;")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._hint)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        self._proceed_btn = QPushButton("Proceed with Encryption →")
        self._proceed_btn.setObjectName("primaryBtn")
        self._proceed_btn.setFixedHeight(36)
        self._proceed_btn.setEnabled(False)
        self._proceed_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._proceed_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self._proceed_btn)
        lay.addLayout(btn_row)

        # Poll timer
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

    def _refresh(self) -> None:
        try:
            from mouse_entropy import get_entropy_pool_status
            st = get_entropy_pool_status()
            pct = int(st.get("percentage", 0))
            ready = bool(st.get("is_ready", False))
        except Exception:
            pct, ready = 0, False

        self._prog.setValue(pct)
        self._pct_lbl.setText(f"{pct} %")

        if ready:
            self._proceed_btn.setEnabled(True)
            self._hint.setText("✓ Entropy collected — click Proceed to encrypt")
            self._hint.setStyleSheet(
                f"color: {_SECURE}; font-size: 11px; font-weight: 600; border: none; background: transparent;"
            )
            self._prog.setStyleSheet(
                f"QProgressBar {{ background: {_SURFACE2}; border: 1px solid {_BORDER}; border-radius: 5px; }}"
                f"QProgressBar::chunk {{ background: {_SECURE}; border-radius: 5px; }}"
            )
        else:
            self._proceed_btn.setEnabled(False)


# ── Pages ──────────────────────────────────────────────────────────────────

class FilesPage(QWidget):
    """Encrypt / decrypt operations."""

    encrypt_requested = pyqtSignal(str)
    decrypt_requested = pyqtSignal(str)
    decrypt_to_disk_requested = pyqtSignal(str)

    def __init__(self, core=None, parent=None):
        super().__init__(parent)
        self._core = core
        self._selected: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # ── Drop zone card ──
        drop_card = Card("Drop & Encrypt")
        self._drop = DropZone()
        self._drop.file_dropped.connect(self._on_file)
        drop_card.body.addWidget(self._drop)

        # Action row
        action_row = QHBoxLayout()
        self._enc_btn = QPushButton("⚿  Encrypt")
        self._enc_btn.setObjectName("primaryBtn")
        self._enc_btn.setEnabled(False)
        self._enc_btn.setFixedHeight(40)
        self._enc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._enc_btn.clicked.connect(self._on_encrypt)

        self._dec_btn = QPushButton("🔓  Open in Sandbox")
        self._dec_btn.setEnabled(False)
        self._dec_btn.setFixedHeight(40)
        self._dec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dec_btn.clicked.connect(self._on_decrypt_browse)

        action_row.addWidget(self._enc_btn)
        action_row.addWidget(self._dec_btn)
        drop_card.body.addLayout(action_row)

        # Decrypt-to-disk row (separate — different security posture)
        disk_row = QHBoxLayout()
        self._disk_btn = QPushButton("💾  Decrypt & Save to Disk…")
        self._disk_btn.setEnabled(False)
        self._disk_btn.setFixedHeight(36)
        self._disk_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._disk_btn.setToolTip(
            "Decrypt a .sffs file and save the plaintext directly to your chosen location.\n"
            "⚠ The decrypted file will NOT be automatically wiped — handle with care."
        )
        self._disk_btn.clicked.connect(self._on_decrypt_to_disk)
        disk_row.addStretch()
        disk_row.addWidget(self._disk_btn)
        drop_card.body.addLayout(disk_row)

        # Progress + status
        self._prog = QProgressBar()
        self._prog.setVisible(False)
        self._prog.setMaximum(100)
        self._prog.setFixedHeight(8)
        drop_card.body.addWidget(self._prog)

        self._status = QLabel("Select a file above to get started")
        self._status.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; border: none; background: transparent;")
        self._status.setWordWrap(True)
        drop_card.body.addWidget(self._status)

        root.addWidget(drop_card)

        # ── Entropy meter card ──
        if core is not None:
            ent_card = Card("Key Entropy")
            ent_row = QHBoxLayout()
            ent_icon = QLabel("🎲")
            ent_icon.setStyleSheet("border: none; background: transparent;")
            ent_row.addWidget(ent_icon)

            ent_info = QVBoxLayout()
            ent_lbl = QLabel("Mouse movement entropy")
            ent_lbl.setStyleSheet(f"color: {_TEXT}; font-size: 12px; border: none; background: transparent;")
            self._ent_bar = QProgressBar()
            self._ent_bar.setObjectName("entropyBar")
            self._ent_bar.setMaximum(100)
            self._ent_bar.setValue(0)
            self._ent_bar.setFixedHeight(8)
            self._ent_hint = QLabel("Move your mouse to strengthen encryption keys")
            self._ent_hint.setStyleSheet(f"color: {_TEXT2}; font-size: 11px; border: none; background: transparent;")
            ent_info.addWidget(ent_lbl)
            ent_info.addWidget(self._ent_bar)
            ent_info.addWidget(self._ent_hint)

            ent_row.addLayout(ent_info)
            ent_card.body.addLayout(ent_row)
            root.addWidget(ent_card)

            # Entropy timer
            self._ent_timer = QTimer(self)
            self._ent_timer.setInterval(500)
            self._ent_timer.timeout.connect(self._refresh_entropy)
            self._ent_timer.start()

        root.addStretch()

    def _on_file(self, path: str) -> None:
        self._selected = path
        self._enc_btn.setEnabled(True)
        self._dec_btn.setEnabled(True)
        self._disk_btn.setEnabled(True)
        self._status.setText(f"Selected: {Path(path).name}")
        self._status.setStyleSheet(f"color: {_TEXT}; font-size: 12px; border: none; background: transparent;")

    def _on_encrypt(self) -> None:
        if self._selected:
            self.encrypt_requested.emit(self._selected)

    def _on_decrypt_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open SFFS file", "", "SFFS encrypted (*.sffs)")
        if path:
            self.decrypt_requested.emit(path)

    def _on_decrypt_to_disk(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose .sffs to decrypt", "", "SFFS encrypted (*.sffs)")
        if path:
            self.decrypt_to_disk_requested.emit(path)

    def set_progress(self, pct: int) -> None:
        self._prog.setVisible(True)
        self._prog.setValue(pct)

    def set_status(self, msg: str, ok: bool = True) -> None:
        color = _SECURE if ok else _DANGER
        self._status.setStyleSheet(f"color: {color}; font-size: 12px; border: none; background: transparent;")
        self._status.setText(msg)

    def _refresh_entropy(self) -> None:
        if self._core is None:
            return
        try:
            from mouse_entropy import get_entropy_pool_status
            st = get_entropy_pool_status()
            pct = st.get("percentage", 0)
            ready = st.get("is_ready", False)
            self._ent_bar.setValue(pct)
            self._ent_bar.setProperty("ready", "true" if ready else "false")
            self._ent_bar.style().unpolish(self._ent_bar)
            self._ent_bar.style().polish(self._ent_bar)
            if ready:
                self._ent_hint.setText("✓ Entropy ready — encryption keys fully randomized")
                self._ent_hint.setStyleSheet(f"color: {_SECURE}; font-size: 11px; border: none; background: transparent;")
            else:
                self._ent_hint.setText(f"Move your mouse to strengthen keys… {pct}%")
                self._ent_hint.setStyleSheet(f"color: {_TEXT2}; font-size: 11px; border: none; background: transparent;")
        except Exception:
            pass

    def mouseMoveEvent(self, e) -> None:
        if self._core is not None:
            try:
                from mouse_entropy import feed_mouse_entropy
                feed_mouse_entropy(e.pos().x(), e.pos().y())
            except Exception:
                pass
        super().mouseMoveEvent(e)


class VaultPage(QWidget):
    """Sandbox decrypted files viewer."""

    def __init__(self, core=None, parent=None):
        super().__init__(parent)
        self._core = core

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Header row
        hdr = QHBoxLayout()
        info = QLabel("Files decrypted into the secure sandbox are listed below. They are automatically wiped on session end.")
        info.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; border: none; background: transparent;")
        info.setWordWrap(True)
        hdr.addWidget(info, 1)
        ref_btn = QPushButton("↻  Refresh")
        ref_btn.setFixedHeight(34)
        ref_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ref_btn.clicked.connect(self.refresh)
        hdr.addWidget(ref_btn)
        root.addLayout(hdr)

        # Sandbox files card
        vault_card = Card("Sandbox Files")
        self._list = QListWidget()
        self._list.setMinimumHeight(240)
        self._list.setAlternatingRowColors(False)
        self._list.itemDoubleClicked.connect(self._open_item)
        vault_card.body.addWidget(self._list)

        open_row = QHBoxLayout()
        self._open_btn = QPushButton("🔍  Open in Viewer")
        self._open_btn.setObjectName("primaryBtn")
        self._open_btn.setEnabled(False)
        self._open_btn.setFixedHeight(38)
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.clicked.connect(self._open_selected)

        browse_sffs = QPushButton("📂  Open .sffs File")
        browse_sffs.setFixedHeight(38)
        browse_sffs.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_sffs.clicked.connect(self._browse_sffs)

        open_row.addWidget(self._open_btn)
        open_row.addWidget(browse_sffs)
        vault_card.body.addLayout(open_row)

        self._vault_status = QLabel("")
        self._vault_status.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; border: none; background: transparent;")
        vault_card.body.addWidget(self._vault_status)

        root.addWidget(vault_card)

        # Sandbox path indicator
        path_card = Card("Sandbox Location")
        self._path_lbl = QLabel("No active session")
        self._path_lbl.setStyleSheet(
            f"color: {_TEAL}; font-family: 'Consolas','Cascadia Code',monospace; "
            f"font-size: 11px; border: none; background: transparent;"
        )
        self._path_lbl.setWordWrap(True)
        path_card.body.addWidget(self._path_lbl)
        path_note = QLabel("All files in this directory are erased when you end the session.")
        path_note.setStyleSheet(f"color: {_TEXT2}; font-size: 11px; border: none; background: transparent;")
        path_card.body.addWidget(path_note)
        root.addWidget(path_card)

        root.addStretch()

        self._list.itemSelectionChanged.connect(
            lambda: self._open_btn.setEnabled(len(self._list.selectedItems()) > 0)
        )
        self.refresh()

    def refresh(self) -> None:
        self._list.clear()
        if self._core is None:
            self._path_lbl.setText("Demo mode — no core attached")
            return
        if hasattr(self._core, "sandbox") and self._core.sandbox:
            dec_dir = Path(self._core.sandbox["decrypted_dir"])
            self._path_lbl.setText(str(dec_dir))
            for p in self._core.list_sandbox_files():
                item = QListWidgetItem(f"  📄  {p.name}")
                item.setData(Qt.ItemDataRole.UserRole, str(p))
                item.setToolTip(str(p))
                self._list.addItem(item)
            count = self._list.count()
            self._vault_status.setText(
                f"{'No files' if count == 0 else str(count) + ' file(s)'} in sandbox"
            )
        else:
            self._path_lbl.setText("No active sandbox")

    def _open_item(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole) or item.text().strip().lstrip("📄").strip()
        self._view_path(path)

    def _open_selected(self) -> None:
        items = self._list.selectedItems()
        if items:
            self._open_item(items[0])

    def _view_path(self, path: str) -> None:
        from sandbox_viewer import show_sandbox_file_viewer
        result = show_sandbox_file_viewer(self, Path(path))
        if result == "external":
            self._vault_status.setText(f"Opened in secure viewer: {Path(path).name}")
        elif result == "inline":
            self._vault_status.setText(f"Previewed inline: {Path(path).name}")
        elif result == "error":
            self._vault_status.setText("Could not open file.")

    def _browse_sffs(self) -> None:
        if self._core is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open SFFS file", "", "SFFS encrypted (*.sffs)")
        if not path:
            return
        try:
            out = self._core.ensure_decrypted_for_view(Path(path))
            self.refresh()
            self._view_path(str(out))
        except Exception as e:
            QMessageBox.warning(self, "Open failed", str(e))


class SecurityPage(QWidget):
    """OS isolation status, process monitor, entropy, audit log tail."""

    def __init__(self, core=None, parent=None):
        super().__init__(parent)
        self._core = core

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # ── Isolation status ──
        iso_card = Card("OS Isolation")
        iso_grid = QGridLayout()
        iso_grid.setSpacing(8)

        self._iso_badge = Badge("Checking…", "neutral")
        self._iso_badge.setFixedHeight(28)
        iso_grid.addWidget(QLabel("Status"), 0, 0)
        iso_grid.addWidget(self._iso_badge, 0, 1)

        self._iso_mode = QLabel("—")
        self._iso_mode.setStyleSheet(f"color: {_TEXT}; border: none; background: transparent;")
        iso_grid.addWidget(QLabel("Mode"), 1, 0)
        iso_grid.addWidget(self._iso_mode, 1, 1)

        self._iso_reason = QLabel("—")
        self._iso_reason.setStyleSheet(f"color: {_TEXT2}; font-size: 11px; border: none; background: transparent;")
        self._iso_reason.setWordWrap(True)
        iso_grid.addWidget(QLabel("Detail"), 2, 0)
        iso_grid.addWidget(self._iso_reason, 2, 1)

        for r in range(3):
            lbl = iso_grid.itemAtPosition(r, 0).widget()
            lbl.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; border: none; background: transparent;")

        iso_card.body.addLayout(iso_grid)
        root.addWidget(iso_card)

        # ── Process monitor ──
        proc_card = Card("Process Monitor")
        self._proc_status = QLabel("No threats detected")
        self._proc_status.setStyleSheet(f"color: {_SECURE}; font-weight: 600; border: none; background: transparent;")
        self._debugger_lbl = QLabel("Debugger: not detected")
        self._debugger_lbl.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; border: none; background: transparent;")
        proc_card.body.addWidget(self._proc_status)
        proc_card.body.addWidget(self._debugger_lbl)
        root.addWidget(proc_card)

        # ── Audit log ──
        log_card = Card("Audit Log  (last 10 events)")
        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMinimumHeight(160)
        self._log_view.setPlaceholderText("No log entries yet…")
        log_card.body.addWidget(self._log_view)
        root.addWidget(log_card)

        # Refresh timer
        self._timer = QTimer(self)
        self._timer.setInterval(3000)
        self._timer.timeout.connect(self._refresh_all)
        self._timer.start()

        root.addStretch()
        self._refresh_all()

    def _refresh_all(self) -> None:
        self._refresh_isolation()
        self._refresh_procs()
        self._refresh_logs()

    def _refresh_isolation(self) -> None:
        try:
            from os_isolation import detect_isolation
            st = detect_isolation()
            if st.get("active"):
                self._iso_badge.set_text_kind("● ISOLATED", "secure")
            else:
                self._iso_badge.set_text_kind("⚠ NOT ISOLATED", "warn")
            self._iso_mode.setText(st.get("mode", "—").replace("_", " ").title())
            self._iso_reason.setText(st.get("reason", "—"))
        except Exception as e:
            self._iso_badge.set_text_kind("ERROR", "danger")
            self._iso_reason.setText(str(e))

    def _refresh_procs(self) -> None:
        try:
            from f10_monitor_process import checkSuspiciousProcesses, isDebuggerPresent
            threats = checkSuspiciousProcesses()
            dbg = isDebuggerPresent()
            if threats or dbg:
                self._proc_status.setText(f"⚠  {len(threats)} suspicious process(es) detected")
                self._proc_status.setStyleSheet(f"color: {_DANGER}; font-weight: 600; border: none; background: transparent;")
            else:
                self._proc_status.setText("✓  No threats detected")
                self._proc_status.setStyleSheet(f"color: {_SECURE}; font-weight: 600; border: none; background: transparent;")
            self._debugger_lbl.setText(
                f"Debugger: {'⚠ DETECTED' if dbg else '✓ not detected'}"
            )
            self._debugger_lbl.setStyleSheet(
                f"color: {_DANGER if dbg else _TEXT2}; font-size: 12px; border: none; background: transparent;"
            )
        except Exception:
            pass

    def _refresh_logs(self) -> None:
        if self._core is None or self._core.logger is None:
            return
        try:
            rows = self._core.logger.viewLogs(limit=10)
            lines = []
            for r in rows:
                ts = r.get("timestamp", "")[:19]
                ev = r.get("event", "")
                sev = r.get("severity", "")
                sev_tag = f"[{sev}]" if sev else ""
                lines.append(f"{ts}  {sev_tag:<8}  {ev}")
            self._log_view.setPlainText("\n".join(lines))
        except Exception:
            pass

    def show_alert(self, message: str, severity: str) -> None:
        color = _DANGER if severity.upper() == "CRITICAL" else _WARN
        self._proc_status.setStyleSheet(f"color: {color}; font-weight: 600; border: none; background: transparent;")
        self._proc_status.setText(f"⚠  {message}")


class SettingsPage(QWidget):
    """Config overview — read-only display of active settings."""

    def __init__(self, core=None, paths: dict | None = None, parent=None):
        super().__init__(parent)
        self._core = core

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # ── Storage info ──
        store_card = Card("Storage")
        self._store_grid = QGridLayout()
        self._store_grid.setSpacing(8)
        self._store_rows: dict[str, QLabel] = {}
        labels = [
            ("USB Free Space", f"{paths.get('free_space_gb', '?')} GB" if paths else "—"),
            ("Data Directory", str(paths.get("data_dir", "—")) if paths else "—"),
            ("Keys Directory", str(paths.get("keys_dir", "—")) if paths else "—"),
        ]
        for i, (k, v) in enumerate(labels):
            key_lbl = QLabel(k)
            key_lbl.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; border: none; background: transparent;")
            val_lbl = QLabel(v)
            val_lbl.setStyleSheet(f"color: {_TEXT}; font-size: 12px; border: none; background: transparent;")
            val_lbl.setWordWrap(True)
            val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._store_grid.addWidget(key_lbl, i, 0)
            self._store_grid.addWidget(val_lbl, i, 1)
        store_card.body.addLayout(self._store_grid)
        root.addWidget(store_card)

        # ── Config values ──
        cfg_card = Card("Active Configuration")
        self._cfg_text = QTextEdit()
        self._cfg_text.setReadOnly(True)
        self._cfg_text.setMinimumHeight(180)
        if core is not None and hasattr(core, "config") and core.config:
            import json as _json
            self._cfg_text.setPlainText(_json.dumps(core.config, indent=2, default=str))
        else:
            self._cfg_text.setPlaceholderText("No config loaded")
        cfg_card.body.addWidget(self._cfg_text)
        root.addWidget(cfg_card)

        # ── Cloud backup ──
        cloud_card = Card("Cloud Backup")
        cloud_info = QLabel(
            "Optional: back up encrypted key bundles to Google Drive.\n"
            "Place client_secret.json in the config directory to enable."
        )
        cloud_info.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; border: none; background: transparent;")
        cloud_info.setWordWrap(True)
        cloud_card.body.addWidget(cloud_info)
        self._cloud_btn = QPushButton("☁  Backup Keys Now")
        self._cloud_btn.setFixedHeight(36)
        self._cloud_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cloud_btn.setEnabled(core is not None)
        self._cloud_btn.clicked.connect(self._do_cloud)
        cloud_card.body.addWidget(self._cloud_btn)

        self._restore_btn = QPushButton("⬇  Restore Keys from Cloud")
        self._restore_btn.setFixedHeight(36)
        self._restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._restore_btn.setToolTip(
            "Lost your USB? Download your backed-up keys from Google Drive\n"
            "to restore decryption capability on this USB."
        )
        self._restore_btn.clicked.connect(self._do_restore)
        cloud_card.body.addWidget(self._restore_btn)
        root.addWidget(cloud_card)

        root.addStretch()

    def _do_cloud(self) -> None:
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
        from PyQt6.QtCore import QThread, pyqtSignal
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

    def _do_restore(self) -> None:
        """Restore keys from Google Drive to this USB (no active session needed)."""
        from f16_cloud_sync import authenticateGoogleDrive, cloudSync, loadCredentials

        # Resolve config/keys dirs — use core paths if logged in, else sffs_data defaults
        if self._core and self._core.paths:
            config_dir = self._core.paths["config_dir"]
            keys_dir = self._core.paths["keys_dir"]
        else:
            from f13_init_drive_detection import initDriveDetection
            paths = initDriveDetection()
            config_dir = paths["config_dir"]
            keys_dir = paths["keys_dir"]

        # Ensure authenticated
        creds = loadCredentials(config_dir)
        if creds is None or not creds.valid:
            reply = QMessageBox.question(
                self, "Connect to Google Drive",
                "Restoring keys requires Google sign-in.\nOpen browser to connect?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            try:
                authenticateGoogleDrive(config_dir)
            except Exception as e:
                QMessageBox.critical(self, "Auth Failed", str(e))
                return

        # List available backups
        lst = cloudSync("list", config_dir=config_dir)
        if lst.get("status") != "ok":
            QMessageBox.warning(self, "Cloud Restore", f"Could not list backups:\n{lst.get('message', lst)}")
            return

        files = lst.get("files", [])
        if not files:
            QMessageBox.information(self, "Cloud Restore", "No backups found in SFFS_Backup on Google Drive.")
            return

        # Build selection dialog
        from PyQt6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Restore Keys from Cloud")
        dlg.setMinimumWidth(480)
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Select a backup to restore:"))
        lst_widget = QListWidget()
        for f in files:
            item = QListWidgetItem(f"{f['name']}   ({f.get('modified','')[:10]}   {int(f.get('size') or 0)//1024} KB)")
            item.setData(Qt.ItemDataRole.UserRole, f["file_id"])
            lst_widget.addItem(item)
        lst_widget.setCurrentRow(0)
        layout.addWidget(lst_widget)

        warn = QLabel(
            "Your .sffs encrypted files must be placed on this USB separately.\n"
            "Keys alone restore decryption capability — not the files themselves."
        )
        warn.setWordWrap(True)
        warn.setStyleSheet("color: #f28b82; font-size: 12px;")
        layout.addWidget(warn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        selected = lst_widget.currentItem()
        if selected is None:
            return
        file_id = selected.data(Qt.ItemDataRole.UserRole)

        # Confirm overwrite if keys already exist
        if keys_dir.exists() and any(keys_dir.iterdir()):
            reply = QMessageBox.warning(
                self, "Overwrite Keys?",
                f"Keys already exist in:\n{keys_dir}\n\nOverwrite with cloud backup?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Run restore in background thread
        from PyQt6.QtCore import QThread, pyqtSignal
        from PyQt6.QtWidgets import QProgressDialog

        core = self._core

        class _RestoreWorker(QThread):
            finished = pyqtSignal(dict)

            def __init__(self, fid, cfg, kdir):
                super().__init__()
                self._fid = fid
                self._cfg = cfg
                self._kdir = kdir

            def run(self):
                if core is not None:
                    result = core.restoreKeysFromCloud(self._fid, self._cfg, self._kdir)
                else:
                    # No core instance — use cloudSync directly
                    import zipfile, tempfile
                    from pathlib import Path as _Path
                    tmp = _Path(tempfile.mktemp(suffix=".zip"))
                    try:
                        r = cloudSync("download", file_id=self._fid, local_path=tmp, config_dir=self._cfg)
                        if r.get("status") != "downloaded":
                            self.finished.emit(r)
                            return
                        self._kdir.mkdir(parents=True, exist_ok=True)
                        with zipfile.ZipFile(tmp) as zf:
                            for member in zf.namelist():
                                from pathlib import PurePosixPath
                                if PurePosixPath(member).is_absolute() or ".." in member:
                                    self.finished.emit({"status": "error", "message": f"Unsafe path: {member}"})
                                    return
                            zf.extractall(self._kdir)
                        result = {"status": "restored", "keys_dir": str(self._kdir)}
                    finally:
                        tmp.unlink(missing_ok=True)
                    self.finished.emit(result)
                    return
                self.finished.emit(result)

        self._restore_worker = _RestoreWorker(file_id, config_dir, keys_dir)
        prog = QProgressDialog("Downloading keys from Google Drive...", None, 0, 0, self)
        prog.setWindowTitle("Restoring Keys")
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        self._restore_prog = prog

        def _on_restore_done(result):
            prog.close()
            if result.get("status") == "restored":
                QMessageBox.information(
                    self, "Restore Complete",
                    f"Keys restored successfully to:\n{result['keys_dir']}\n\n"
                    "Place your .sffs files on this USB and log in to decrypt them."
                )
            else:
                QMessageBox.critical(
                    self, "Restore Failed",
                    f"Could not restore keys:\n{result.get('message', result)}"
                )

        self._restore_worker.finished.connect(_on_restore_done)
        self._restore_worker.start()
        prog.exec()


# ── Main dashboard window ──────────────────────────────────────────────────

class SFFSWindow(QMainWindow):
    """
    Modern SFFS main window.

    Layout:
        TopBar (56px fixed)
        ├── Sidebar (200px fixed)
        └── QStackedWidget (fills remaining space)
            ├── [0] FilesPage
            ├── [1] VaultPage
            ├── [2] SecurityPage
            └── [3] SettingsPage
    """

    PAGE_TITLES = ["Files", "Vault", "Security", "Settings"]

    def __init__(
        self,
        session_token: str,
        config: dict,
        paths: dict,
        core=None,
        username: str = "user",
        on_logout=None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("SFFS — Smart File Fortify System")
        self.setMinimumSize(1040, 680)
        self._core = core
        self._on_logout = on_logout
        self._username = username

        # ── Root widget ──
        root_w = QWidget()
        self.setCentralWidget(root_w)
        root_lay = QVBoxLayout(root_w)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # Top bar
        self._topbar = TopBar(username)
        self._topbar.end_session.connect(self._do_logout)
        root_lay.addWidget(self._topbar)

        # Content row
        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._switch_page)
        content_row.addWidget(self._sidebar)

        # Pages stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {_BG};")

        self._files_page = FilesPage(core)
        self._files_page.encrypt_requested.connect(self._do_encrypt)
        self._files_page.decrypt_requested.connect(self._do_decrypt)
        self._files_page.decrypt_to_disk_requested.connect(self._do_decrypt_to_disk)

        self._vault_page = VaultPage(core)
        self._security_page = SecurityPage(core)
        self._settings_page = SettingsPage(core, paths)

        for p in (self._files_page, self._vault_page, self._security_page, self._settings_page):
            self._stack.addWidget(p)

        content_row.addWidget(self._stack, 1)

        container = QWidget()
        container.setLayout(content_row)
        root_lay.addWidget(container, 1)

        # Mouse tracking for entropy on all pages
        self.setMouseTracking(True)
        root_w.setMouseTracking(True)

    def _switch_page(self, idx: int) -> None:
        self._stack.setCurrentIndex(idx)
        self._topbar.set_page(self.PAGE_TITLES[idx])

    def _do_logout(self) -> None:
        if self._on_logout:
            self._on_logout()
        else:
            self.close()

    def updateProgress(self, percent: int) -> None:
        self._files_page.set_progress(percent)

    def showSecurityAlert(self, message: str, severity: str) -> None:
        kind = "danger" if severity.upper() == "CRITICAL" else "warn"
        self._topbar.set_security(f"⚠ {message[:30]}", kind)
        self._security_page.show_alert(message, severity)

    def set_security_status(self, text: str, kind: str) -> None:
        self._topbar.set_security(text, kind)

    def mouseMoveEvent(self, e) -> None:
        if self._core is not None:
            try:
                from mouse_entropy import feed_mouse_entropy
                feed_mouse_entropy(e.pos().x(), e.pos().y())
            except Exception:
                pass
        super().mouseMoveEvent(e)

    def _do_encrypt(self, path: str) -> None:
        if self._core is None:
            self._files_page.set_status("Demo mode — no core attached", False)
            return
        # VeraCrypt-style: require entropy collection before proceeding
        try:
            from mouse_entropy import is_entropy_ready
            need_dialog = not is_entropy_ready()
        except Exception:
            need_dialog = False
        if need_dialog:
            dlg = EntropyCollectorDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                self._files_page.set_status("Encryption cancelled — entropy collection aborted", False)
                return
        try:
            self._files_page.set_progress(10)
            result = self._core.encryptFileOperation(Path(path))
            self._files_page.set_progress(100)
            out = Path(result.get("sffs_path", path))
            self._files_page.set_status(f"✓ Encrypted → {out.name}", True)
        except Exception as e:
            self._files_page.set_status(f"Encrypt failed: {e}", False)
            QMessageBox.warning(self, "Encrypt failed", str(e))

    def _do_decrypt(self, path: str) -> None:
        if self._core is None:
            self._files_page.set_status("Demo mode — no core attached", False)
            return
        try:
            self._files_page.set_progress(10)
            result = self._core.decryptFileOperation(Path(path))
            self._files_page.set_progress(100)
            out = Path(result.get("output_path", path))
            self._files_page.set_status(f"✓ Decrypted → sandbox/{out.name}", True)
            self._vault_page.refresh()
            self._switch_page(1)   # jump to Vault
            self._sidebar._select(1)
        except Exception as e:
            self._files_page.set_status(f"Decrypt failed: {e}", False)
            QMessageBox.warning(self, "Decrypt failed", str(e))

    def _do_decrypt_to_disk(self, sffs_path: str) -> None:
        """Decrypt a .sffs file and save plaintext directly to a user-chosen disk location."""
        if self._core is None:
            self._files_page.set_status("Demo mode — no core attached", False)
            return

        # Security warning — decrypted file is NOT auto-wiped
        warn = QMessageBox(self)
        warn.setIcon(QMessageBox.Icon.Warning)
        warn.setWindowTitle("⚠ Decrypt to Disk — Security Notice")
        warn.setText(
            "<b>The decrypted file will be saved to your disk and will NOT be automatically wiped.</b><br><br>"
            "Unlike the secure sandbox, files saved to disk persist until you manually delete them. "
            "Forensic tools can recover deleted files.<br><br>"
            "Only proceed if you need the plaintext file outside SFFS."
        )
        warn.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        warn.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if warn.exec() != QMessageBox.StandardButton.Ok:
            return

        # Pick save location
        stem = Path(sffs_path).stem  # e.g. "report" from "report.sffs"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Decrypted File As…", stem, "All Files (*)"
        )
        if not save_path:
            return

        try:
            self._files_page.set_progress(10)
            result = self._core.decryptFileOperation(
                Path(sffs_path), output_path=Path(save_path)
            )
            self._files_page.set_progress(100)
            out = Path(result.get("output_path", save_path))
            self._files_page.set_status(f"✓ Saved plaintext → {out.name}", True)
            QMessageBox.information(
                self,
                "Decrypt to Disk — Done",
                f"File saved to:\n{out}\n\n"
                "Remember: this file is NOT protected by the SFFS sandbox. "
                "Delete it securely when no longer needed.",
            )
        except Exception as e:
            self._files_page.set_status(f"Decrypt to disk failed: {e}", False)
            QMessageBox.warning(self, "Decrypt to Disk failed", str(e))


# ── Login window ───────────────────────────────────────────────────────────

class LoginWindow(QDialog):
    """Modern login dialog — centered card, shield emblem."""

    def __init__(self, paths: dict, core=None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SFFS — Secure Login")
        self.setFixedSize(420, 560)
        self._paths = paths
        self._core = core          # if provided, core.login() is used
        self._token: str | None = None
        self._username: str = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Background
        bg = QFrame()
        bg.setStyleSheet(f"QFrame {{ background: {_BG}; }}")
        bg_lay = QVBoxLayout(bg)
        bg_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Card
        card = QFrame()
        card.setFixedWidth(340)
        card.setStyleSheet(
            f"QFrame {{ background: {_SURFACE}; border: 1px solid {_BORDER}; border-radius: 16px; }}"
        )
        card.setGraphicsEffect(_shadow(24, 100))
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(32, 32, 32, 32)
        card_lay.setSpacing(16)
        card_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Shield emblem
        shield = QLabel("🔐")
        shield.setFont(_bold(36))
        shield.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shield.setStyleSheet("border: none; background: transparent;")
        card_lay.addWidget(shield)

        title = QLabel("SFFS")
        title.setFont(_bold(20))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {_TEXT}; border: none; background: transparent;")
        card_lay.addWidget(title)

        sub = QLabel("Smart File Fortify System")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; border: none; background: transparent;")
        card_lay.addWidget(sub)

        card_lay.addWidget(Divider())

        # Form
        user_lbl = QLabel("Username")
        user_lbl.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        card_lay.addWidget(user_lbl)

        self._user = QLineEdit()
        self._user.setPlaceholderText("Enter username")
        self._user.setFixedHeight(42)
        card_lay.addWidget(self._user)

        pw_lbl = QLabel("Password")
        pw_lbl.setStyleSheet(f"color: {_TEXT2}; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        card_lay.addWidget(pw_lbl)

        self._pw = QLineEdit()
        self._pw.setPlaceholderText("Enter password")
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw.setFixedHeight(42)
        self._pw.returnPressed.connect(self._try_login)
        card_lay.addWidget(self._pw)

        self._err = QLabel("")
        self._err.setStyleSheet(f"color: {_DANGER}; font-size: 11px; border: none; background: transparent;")
        self._err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err.setWordWrap(True)
        card_lay.addWidget(self._err)

        login_btn = QPushButton("Unlock")
        login_btn.setObjectName("primaryBtn")
        login_btn.setFixedHeight(44)
        login_btn.setFont(_semibold(13))
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.clicked.connect(self._try_login)
        card_lay.addWidget(login_btn)

        # Register link row
        reg_row = QHBoxLayout()
        reg_lbl = QLabel("New user?")
        reg_lbl.setStyleSheet(f"color: {_TEXT2}; font-size: 11px; border: none; background: transparent;")
        reg_btn = QPushButton("Register account")
        reg_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {_ACCENT}; "
            f"font-size: 11px; padding: 0; text-decoration: underline; }}"
            f"QPushButton:hover {{ color: #58a6ff; }}"
        )
        reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reg_btn.clicked.connect(self._try_register)
        reg_row.addStretch()
        reg_row.addWidget(reg_lbl)
        reg_row.addWidget(reg_btn)
        reg_row.addStretch()
        card_lay.addLayout(reg_row)

        # Security note
        note = QLabel("🔒  All credentials stay on-device")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet(f"color: {_TEXT2}; font-size: 10px; border: none; background: transparent;")
        card_lay.addWidget(note)

        bg_lay.addWidget(card)
        outer.addWidget(bg)

    def _inject_paths(self) -> None:
        for sub in ("code1", "code2", "code3", "main-code"):
            p = str(Path(__file__).resolve().parent.parent / sub)
            if p not in sys.path:
                sys.path.insert(0, p)

    def _try_login(self) -> None:
        self._inject_paths()
        username = self._user.text().strip()
        password = self._pw.text()
        if not username or not password:
            self._err.setText("Username and password are required")
            return

        if self._core is not None:
            # Use core.login() so sandbox + session state are fully initialised
            r = self._core.login(username, bytearray(password.encode()))
            if r.get("authenticated"):
                self._token = self._core.session_token
                self._username = username
                self.accept()
            else:
                self._err.setText(r.get("message", "Invalid username or password"))
                self._pw.clear()
                self._pw.setFocus()
        else:
            from f09_authenticate_user import authenticateUser, initAuthDatabase
            db = Path(self._paths["data_dir"]) / "auth.db"
            initAuthDatabase(db)
            r = authenticateUser(username, bytearray(password.encode()), db)
            if r.get("authenticated"):
                self._token = r.get("session_token")
                self._username = username
                self.accept()
            else:
                self._err.setText(r.get("message", "Invalid username or password"))
                self._pw.clear()
                self._pw.setFocus()

    def _try_register(self) -> None:
        self._inject_paths()
        from f09_authenticate_user import initAuthDatabase, registerUser
        username = self._user.text().strip()
        password = self._pw.text()
        if not username or not password:
            self._err.setText("Fill username and password before registering")
            return
        db = Path(self._paths["data_dir"]) / "auth.db"
        initAuthDatabase(db)
        try:
            r = registerUser(username, bytearray(password.encode()), db)
        except ValueError as e:
            self._err.setText(str(e))
            return
        if r.get("status") == "registered":
            self._err.setStyleSheet(
                f"color: {_SECURE}; font-size: 11px; border: none; background: transparent;"
            )
            self._err.setText("✓ Account created — click Unlock to log in")
        else:
            self._err.setText(r.get("message", "Registration failed"))

    @property
    def session_token(self) -> str | None:
        return self._token

    @property
    def username(self) -> str:
        return self._username


# ── Public entry points ────────────────────────────────────────────────────

def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(STYLESHEET)


def run_modern_ui(
    core,
    paths: dict,
    config: dict,
    username: str = "user",
    session_token: str = "",
    on_logout=None,
) -> None:
    """
    Launch the modern dashboard. Called by main.py after successful login.
    Reuses existing QApplication if present.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app)
    win = SFFSWindow(session_token, config, paths, core, username, on_logout)
    win.show()

    # Bootstrap security status
    try:
        from os_isolation import detect_isolation
        st = detect_isolation()
        if st.get("active"):
            win.set_security_status("● SECURE", "secure")
        else:
            win.set_security_status("⚠ NO ISOLATION", "warn")
    except Exception:
        pass

    app.exec()


# ── Standalone demo ────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        apply_theme(app)
    except Exception as e:
        print("No display available:", e)
        sys.exit(0)

    _ROOT = Path(__file__).resolve().parent.parent
    for _p in (_ROOT / "code1", _ROOT / "code2", _ROOT / "code3", _ROOT / "main-code"):
        s = str(_p)
        if s not in sys.path:
            sys.path.insert(0, s)

    demo_paths = {
        "data_dir": _ROOT / "sffs_data" / "data",
        "keys_dir": _ROOT / "sffs_data" / "keys",
        "free_space_gb": 4.2,
    }
    (demo_paths["data_dir"]).mkdir(parents=True, exist_ok=True)

    # Show login first
    login = LoginWindow(demo_paths)
    login.setStyleSheet(STYLESHEET)
    if login.exec() == QDialog.DialogCode.Accepted and login.session_token:
        try:
            from sffs_core import SFFSCore
            core = SFFSCore()
            core.initialize()
        except Exception:
            core = None

        win = SFFSWindow(
            session_token=login.session_token or "demo",
            config={},
            paths=demo_paths,
            core=core,
            username=login.username or "user",
        )
        win.show()

        try:
            from os_isolation import detect_isolation
            st = detect_isolation()
            win.set_security_status("● SECURE" if st.get("active") else "⚠ NO ISOLATION",
                                    "secure" if st.get("active") else "warn")
        except Exception:
            pass

        app.exec()
    else:
        # Demo without login
        win = SFFSWindow(
            session_token="demo-token",
            config={},
            paths=demo_paths,
            core=None,
            username="demo",
        )
        win.show()
        win.set_security_status("⚠ DEMO MODE", "warn")
        app.exec()
