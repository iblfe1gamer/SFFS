"""Windows Job Object lazy activation when not started via sffs.bat."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows-only")


def test_try_activate_job_sets_isolation_markers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SFFS_OS_ISOLATION", raising=False)
    monkeypatch.delenv("SFFS_JOB_OBJECT_ACTIVE", raising=False)

    import windows_job_wrapper as wjw
    import os_isolation

    assert os_isolation.detect_isolation()["active"] is False

    ok = wjw.try_activate_job_for_current_process()
    assert ok is True
    status = os_isolation.detect_isolation()
    assert status["active"] is True
    assert status["mode"] == "windows_job"


def test_try_activate_job_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SFFS_OS_ISOLATION", raising=False)
    monkeypatch.delenv("SFFS_JOB_OBJECT_ACTIVE", raising=False)

    import windows_job_wrapper as wjw

    assert wjw.try_activate_job_for_current_process() is True
    assert wjw.try_activate_job_for_current_process() is True
