"""
Tests for code3/mouse_entropy.py — mouse-movement entropy pool.

Covers:
  - feed_mouse_entropy grows the pool
  - pool bounded at 8192 bytes
  - session_random_bytes returns correct length (with and without pool)
  - session_random_bytes is non-deterministic
  - get_entropy_pool_status returns correct structure and values
  - is_entropy_ready threshold (256 bytes)
  - thread-safety (concurrent feeds don't corrupt pool)
"""

import threading
import sys
from pathlib import Path

import pytest

# Ensure code3 is on path (conftest already does this, but be explicit)
_ROOT = Path(__file__).resolve().parent.parent
_CODE3 = str(_ROOT / "code3")
if _CODE3 not in sys.path:
    sys.path.insert(0, _CODE3)

import mouse_entropy as me


# ---------------------------------------------------------------------------
# Fixture: reset module-level pool before every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_pool():
    """Clear the internal entropy pool before each test for isolation."""
    with me._lock:
        me._pool.clear()
    yield
    with me._lock:
        me._pool.clear()


# ---------------------------------------------------------------------------
# feed_mouse_entropy
# ---------------------------------------------------------------------------

class TestFeedMouseEntropy:
    def test_feed_grows_pool(self):
        assert len(me._pool) == 0
        me.feed_mouse_entropy(100, 200)
        with me._lock:
            size = len(me._pool)
        # SHA-256 produces 32 bytes per feed
        assert size == 32

    def test_multiple_feeds_accumulate(self):
        for i in range(5):
            me.feed_mouse_entropy(i * 10, i * 20)
        with me._lock:
            size = len(me._pool)
        assert size == 5 * 32

    def test_pool_bounded_at_8192(self):
        # Feed enough to overflow: ceil(8192/32) + 10 = 267 feeds
        for i in range(300):
            me.feed_mouse_entropy(i, i)
        with me._lock:
            size = len(me._pool)
        assert size == 8192

    def test_different_coordinates_produce_different_bytes(self):
        """Two feeds with different coords should (almost always) differ."""
        me.feed_mouse_entropy(0, 0)
        with me._lock:
            chunk_a = bytes(me._pool[:32])
        with me._lock:
            me._pool.clear()
        me.feed_mouse_entropy(999, 888)
        with me._lock:
            chunk_b = bytes(me._pool[:32])
        assert chunk_a != chunk_b

    def test_zero_coordinates_accepted(self):
        me.feed_mouse_entropy(0, 0)
        with me._lock:
            size = len(me._pool)
        assert size == 32

    def test_large_coordinates_accepted(self):
        me.feed_mouse_entropy(99999, 99999)
        with me._lock:
            size = len(me._pool)
        assert size == 32


# ---------------------------------------------------------------------------
# session_random_bytes
# ---------------------------------------------------------------------------

class TestSessionRandomBytes:
    def test_returns_correct_length_no_pool(self):
        for n in (1, 16, 32, 64, 128, 200):
            result = me.session_random_bytes(n)
            assert isinstance(result, bytes)
            assert len(result) == n

    def test_returns_correct_length_with_pool(self):
        # Fill pool first
        for i in range(20):
            me.feed_mouse_entropy(i, i * 3)
        for n in (1, 16, 32, 64, 128):
            result = me.session_random_bytes(n)
            assert len(result) == n

    def test_non_deterministic_without_pool(self):
        """Two consecutive calls must produce different results."""
        a = me.session_random_bytes(32)
        b = me.session_random_bytes(32)
        assert a != b

    def test_non_deterministic_with_pool(self):
        for i in range(20):
            me.feed_mouse_entropy(i, i)
        a = me.session_random_bytes(32)
        b = me.session_random_bytes(32)
        assert a != b

    def test_returns_bytes_type(self):
        result = me.session_random_bytes(16)
        assert type(result) is bytes

    def test_n_equals_1(self):
        result = me.session_random_bytes(1)
        assert len(result) == 1

    def test_n_greater_than_32_without_pool(self):
        result = me.session_random_bytes(100)
        assert len(result) == 100

    def test_n_greater_than_32_with_pool(self):
        for i in range(30):
            me.feed_mouse_entropy(i * 7, i * 13)
        result = me.session_random_bytes(100)
        assert len(result) == 100

    def test_output_not_all_zeros(self):
        result = me.session_random_bytes(32)
        assert result != b"\x00" * 32


# ---------------------------------------------------------------------------
# get_entropy_pool_status
# ---------------------------------------------------------------------------

class TestGetEntropyPoolStatus:
    def test_empty_pool_status(self):
        status = me.get_entropy_pool_status()
        assert status["bytes_collected"] == 0
        assert status["target"] == 256
        assert status["percentage"] == 0
        assert status["is_ready"] is False

    def test_partial_pool_status(self):
        # Feed 4 times = 128 bytes = 50%
        for i in range(4):
            me.feed_mouse_entropy(i * 100, i * 50)
        status = me.get_entropy_pool_status()
        assert status["bytes_collected"] == 128
        assert status["percentage"] == 50
        assert status["is_ready"] is False

    def test_full_pool_status(self):
        # Feed 8 times = 256 bytes = ready
        for i in range(8):
            me.feed_mouse_entropy(i * 7, i * 11)
        status = me.get_entropy_pool_status()
        assert status["bytes_collected"] == 256
        assert status["percentage"] == 100
        assert status["is_ready"] is True

    def test_percentage_capped_at_100(self):
        # Overfill: 300 * 32 = 9600 > 8192
        for i in range(300):
            me.feed_mouse_entropy(i, i)
        status = me.get_entropy_pool_status()
        assert status["percentage"] == 100

    def test_status_keys_present(self):
        status = me.get_entropy_pool_status()
        assert set(status.keys()) == {"bytes_collected", "target", "percentage", "is_ready"}

    def test_target_is_256(self):
        status = me.get_entropy_pool_status()
        assert status["target"] == 256


# ---------------------------------------------------------------------------
# is_entropy_ready
# ---------------------------------------------------------------------------

class TestIsEntropyReady:
    def test_false_when_empty(self):
        assert me.is_entropy_ready() is False

    def test_false_below_threshold(self):
        # 7 feeds = 224 bytes < 256
        for i in range(7):
            me.feed_mouse_entropy(i, i)
        assert me.is_entropy_ready() is False

    def test_true_at_exact_threshold(self):
        # 8 feeds = 256 bytes == _ENTROPY_TARGET
        for i in range(8):
            me.feed_mouse_entropy(i * 13, i * 7)
        assert me.is_entropy_ready() is True

    def test_true_above_threshold(self):
        for i in range(20):
            me.feed_mouse_entropy(i, i)
        assert me.is_entropy_ready() is True

    def test_consistent_with_pool_status(self):
        for i in range(10):
            me.feed_mouse_entropy(i, i)
        status = me.get_entropy_pool_status()
        assert me.is_entropy_ready() == status["is_ready"]


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestThreadSafety:
    def test_concurrent_feeds_no_corruption(self):
        """50 threads each feed 20 times — pool must stay bounded and valid."""
        errors = []

        def feeder(tid):
            try:
                for j in range(20):
                    me.feed_mouse_entropy(tid * 100 + j, j)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=feeder, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        with me._lock:
            size = len(me._pool)
        assert size <= 8192

    def test_concurrent_feed_and_read(self):
        """Feed and session_random_bytes running concurrently must not deadlock or crash."""
        results = []
        errors = []

        def feeder():
            for i in range(100):
                me.feed_mouse_entropy(i, i * 2)

        def reader():
            try:
                for _ in range(50):
                    b = me.session_random_bytes(32)
                    results.append(len(b))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=feeder)] + \
                  [threading.Thread(target=reader) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert all(r == 32 for r in results)
