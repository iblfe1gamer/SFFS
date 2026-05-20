"""
f15_file_manager_explorer.py — SFFS Student 3: Scoped file browser

A host ``QFileDialog`` leaks paths to OS MRU databases and thumbnail caches. A
tree scoped to the USB root keeps browsing inside the vault. Context actions
are labels only in this demo — wiring to crypto belongs in ``main-code``.
"""

from __future__ import annotations

from pathlib import Path

# Why: QFileSystemModel avoids reimplementing directory walks on FAT/exFAT USB
from PyQt6.QtCore import QDir, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileSystemModel,
    QLabel,
    QMenu,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class FileManagerExplorer(QWidget):
    """
    Two-pane explorer: directory tree + shallow file list for the selected dir.
    """

    sffs_file_selected = pyqtSignal(str)
    plain_file_selected = pyqtSignal(str)

    def __init__(self, root_path: Path, allowed_extensions: list[str] | None = None) -> None:
        super().__init__()
        self._root = Path(root_path).resolve()

        self._model = QFileSystemModel()
        self._model.setRootPath(str(self._root))
        self._model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
        self._model.setReadOnly(True)
        if allowed_extensions and "*" not in allowed_extensions:
            patterns = [f"*{e}" if e.startswith(".") else f"*.{e}" for e in allowed_extensions]
            self._model.setNameFilters(patterns)
            self._model.setNameFilterDisables(False)

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setRootIndex(self._model.index(str(self._root)))
        for col in range(1, 4):
            self._tree.hideColumn(col)

        self._list = QTreeView()
        self._list.setModel(self._model)
        self._list.setRootIsDecorated(False)
        self._list.setItemsExpandable(False)
        self._list.setEditTriggers(QAbstractItemView.EditTrigger.NoEdit)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._tree)
        splitter.addWidget(self._list)

        self._status = QLabel(str(self._root))

        vl = QVBoxLayout(self)
        vl.addWidget(splitter)
        vl.addWidget(self._status)

        self._tree.selectionModel().currentChanged.connect(self._on_tree_change)
        self._list.doubleClicked.connect(self._on_double_click)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._ctx_menu)

    def _on_tree_change(self, cur, _prev) -> None:
        path = self._model.filePath(cur)
        self._list.setRootIndex(self._model.index(path))

    def _on_double_click(self, idx) -> None:
        path = Path(self._model.filePath(idx))
        if path.is_dir():
            return
        s = str(path)
        if path.suffix.lower() == ".sffs":
            self.sffs_file_selected.emit(s)
        else:
            self.plain_file_selected.emit(s)
        self._status.setText(f"{s}  ({path.stat().st_size} bytes)")

    def _ctx_menu(self, pos) -> None:
        menu = QMenu(self)
        menu.addAction("Encrypt")
        menu.addAction("Decrypt")
        menu.addAction("Delete")
        menu.exec(self._list.mapToGlobal(pos))


def fileManagerExplorer(root_path: Path, allowed_extensions: list[str] | None = None) -> QWidget:
    """
    Factory returning a configured ``FileManagerExplorer`` widget.

    Args:
        root_path: USB-scoped root directory.
        allowed_extensions: e.g. ``['.sffs']`` or ``None`` for all.

    Returns:
        QWidget hosting the explorer.
    """
    return FileManagerExplorer(root_path, allowed_extensions)


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    try:
        app = QApplication(sys.argv)
    except Exception as e:
        print("No display:", e)
        sys.exit(0)
    w = fileManagerExplorer(Path.cwd(), None)
    w.setWindowTitle("SFFS File Explorer Demo")
    w.resize(900, 500)
    w.show()
    app.exec()
