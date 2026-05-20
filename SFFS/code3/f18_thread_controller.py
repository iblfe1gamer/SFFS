"""
f18_thread_controller.py — SFFS Student 3: Qt worker threads

The GIL still allows concurrent I/O: disk reads during encryption keep the UI
responsive if work runs off the main thread. Qt forbids touching widgets from
background threads; ``pyqtSignal`` is queued onto the GUI thread safely.

Why QThread here:
- Integrates with Qt's event loop and supports cancellation from the UI.
"""

from __future__ import annotations

import functools
import traceback
from typing import Any, Callable

# Why QThread over threading.Thread: signals marshal back to the GUI thread safely
from PyQt6.QtCore import QObject, QThread, pyqtSignal


class WorkerSignals(QObject):
    """Signal bundle emitted from ``WorkerThread``."""

    progress = pyqtSignal(int)
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()
    status_message = pyqtSignal(str)


class WorkerThread(QThread):
    """Runs ``task(*args, **kwargs)`` and emits signals."""

    def __init__(self, task: Callable, args: tuple = (), kwargs: dict | None = None) -> None:
        super().__init__()
        self.task = task
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.signals = WorkerSignals()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def is_cancelled(self) -> bool:
        return self._cancelled

    def run(self) -> None:
        try:
            out = self.task(*self.args, **self.kwargs)
            self.signals.result.emit(out)
        except Exception as e:
            self.signals.error.emit(f"{e}\n{traceback.format_exc()}")
        finally:
            self.signals.finished.emit()


def threadController(
    task: Callable,
    args: tuple = (),
    kwargs: dict | None = None,
    progress_callback=None,
    done_callback=None,
    error_callback=None,
    finished_callback=None,
) -> WorkerThread:
    """
    Start a worker thread and optionally wire callbacks.

    Args:
        task: Callable to run in the thread.
        args: Positional arguments for ``task``.
        kwargs: Keyword arguments for ``task``.
        progress_callback: ``callable(int)`` connected to ``progress`` signal.
        done_callback: ``callable(result)`` on success.
        error_callback: ``callable(str)`` on failure.
        finished_callback: ``callable()`` connected before ``start()`` (e.g. ``app.quit``).

    Returns:
        Started ``WorkerThread`` instance.
    """
    worker = WorkerThread(task, args, kwargs)
    if progress_callback:
        worker.signals.progress.connect(progress_callback)
    if done_callback:
        worker.signals.result.connect(done_callback)
    if error_callback:
        worker.signals.error.connect(error_callback)
    if finished_callback:
        worker.signals.finished.connect(finished_callback)
    worker.start()
    return worker


def run_in_thread(fn: Callable | None = None, *, kwargs: dict | None = None):
    """
    Decorator: return a function that launches ``fn`` in a ``WorkerThread``.

    The returned callable starts the thread and returns the worker handle.
    """

    def decorator(f: Callable):
        @functools.wraps(f)
        def wrapper(*args, **kw):
            merged = dict(kwargs or {})
            merged.update(kw)
            return threadController(f, args=args, kwargs=merged)

        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


if __name__ == "__main__":
    import sys
    import time

    from PyQt6.QtWidgets import QApplication, QProgressBar, QWidget, QVBoxLayout

    try:
        app = QApplication(sys.argv)
    except Exception as e:
        print("No GUI:", e)
        sys.exit(0)

    w = QWidget()
    w.setWindowTitle("SFFS thread demo")
    bar = QProgressBar()
    bar.setRange(0, 100)
    lay = QVBoxLayout(w)
    lay.addWidget(bar)

    holder: list[WorkerThread] = []

    def task_with_progress() -> str:
        for pct in (20, 40, 60, 80, 100):
            time.sleep(0.25)
            holder[0].signals.progress.emit(pct)
            holder[0].signals.status_message.emit(f"{pct}%")
        return "complete"

    worker = WorkerThread(task_with_progress, (), {})
    holder.append(worker)

    def on_prog(p: int) -> None:
        bar.setValue(p)

    worker.signals.progress.connect(on_prog)
    worker.signals.result.connect(lambda r: print("Result:", r))
    worker.signals.finished.connect(app.quit)
    w.show()
    worker.start()
    app.exec()
