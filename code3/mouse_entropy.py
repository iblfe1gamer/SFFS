"""
Mouse movement entropy — mixed with OS CSPRNG for per-session file keys.

WHY: Adds unpredictable user-specific input on top of secrets.token_bytes.
"""

from __future__ import annotations

import hashlib
import secrets
import threading
import time

_lock = threading.Lock()
_pool = bytearray()


def feed_mouse_entropy(x: int, y: int) -> None:
    """Call from GUI mouse-move handler; updates an internal pool (bounded)."""
    t = time.monotonic_ns()
    chunk = hashlib.sha256(f"{x}:{y}:{t}".encode()).digest()
    with _lock:
        _pool.extend(chunk)
        if len(_pool) > 8192:
            del _pool[:-8192]


def session_random_bytes(n: int) -> bytes:
    """
    Cryptographically strong random bytes, XOR-mixed with mouse pool if any.
    """
    base = secrets.token_bytes(max(n, 32))
    with _lock:
        extra = bytes(_pool)
    if not extra:
        return base[:n]
    h = hashlib.sha256(base + extra).digest()
    if n <= 32:
        return h[:n]
    out = bytearray(h)
    i = 32
    while len(out) < n:
        out.extend(hashlib.sha256(bytes(out[-32:]) + extra + base).digest())
    return bytes(out[:n])
