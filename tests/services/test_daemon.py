"""Unit tests for the daemon service (task TP-122, spec docs/specs/0005).

Covers PID file read/write/parse, stale-PID detection, liveness checks, and the
start/stop lifecycle at the service layer, isolated from a real home directory
via an explicit ``registry_dir`` (same isolation shape as ``services/registry.py``).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from taskpilot.services import daemon
from taskpilot.services.errors import ConflictError, NotFound


def _spawn_sleeper() -> subprocess.Popen:
    """A real, easily-killable child process to exercise liveness/termination."""
    return subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
    )


def test_read_state_is_none_when_no_pid_file(tmp_path: Path):
    assert daemon.read_state(tmp_path) is None


def test_is_alive_true_for_running_process_false_after_it_exits():
    proc = _spawn_sleeper()
    try:
        assert daemon.is_alive(proc.pid) is True
    finally:
        proc.terminate()
        proc.wait(timeout=5)
    assert daemon.is_alive(proc.pid) is False


def test_is_alive_false_for_implausible_pid():
    # PID 0 and negative PIDs are never a real daemon child on any supported OS.
    assert daemon.is_alive(-1) is False


def test_read_state_returns_recorded_fields_for_live_process(tmp_path: Path):
    proc = _spawn_sleeper()
    try:
        daemon.write_state(
            tmp_path,
            daemon.DaemonState(
                pid=proc.pid,
                host="127.0.0.1",
                port=7152,
                started_at="2026-07-31T09:00:00Z",
            ),
        )
        state = daemon.read_state(tmp_path)
        assert state is not None
        assert state.pid == proc.pid
        assert state.host == "127.0.0.1"
        assert state.port == 7152
        assert state.started_at == "2026-07-31T09:00:00Z"
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_read_state_cleans_up_stale_pid_file(tmp_path: Path):
    proc = _spawn_sleeper()
    proc.terminate()
    proc.wait(timeout=5)

    daemon.write_state(
        tmp_path,
        daemon.DaemonState(
            pid=proc.pid,
            host="127.0.0.1",
            port=7152,
            started_at="2026-07-31T09:00:00Z",
        ),
    )

    assert daemon.read_state(tmp_path) is None
    assert not daemon.pid_file(tmp_path).exists()


def test_stop_daemon_raises_not_found_when_nothing_running(tmp_path: Path):
    with pytest.raises(NotFound):
        daemon.stop_daemon(tmp_path)


def test_stop_daemon_raises_not_found_and_cleans_stale_file(tmp_path: Path):
    proc = _spawn_sleeper()
    proc.terminate()
    proc.wait(timeout=5)

    daemon.write_state(
        tmp_path,
        daemon.DaemonState(
            pid=proc.pid,
            host="127.0.0.1",
            port=7152,
            started_at="2026-07-31T09:00:00Z",
        ),
    )

    with pytest.raises(NotFound):
        daemon.stop_daemon(tmp_path)
    assert not daemon.pid_file(tmp_path).exists()


def test_stop_daemon_terminates_recorded_process(tmp_path: Path):
    proc = _spawn_sleeper()
    daemon.write_state(
        tmp_path,
        daemon.DaemonState(
            pid=proc.pid,
            host="127.0.0.1",
            port=7152,
            started_at="2026-07-31T09:00:00Z",
        ),
    )

    daemon.stop_daemon(tmp_path)

    assert daemon.is_alive(proc.pid) is False
    assert not daemon.pid_file(tmp_path).exists()


def test_start_daemon_raises_conflict_when_already_running(tmp_path: Path):
    proc = _spawn_sleeper()
    try:
        daemon.write_state(
            tmp_path,
            daemon.DaemonState(
                pid=proc.pid,
                host="127.0.0.1",
                port=7152,
                started_at="2026-07-31T09:00:00Z",
            ),
        )
        with pytest.raises(ConflictError):
            daemon.start_daemon(tmp_path, host="127.0.0.1", port=7152, workspace=None)
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_log_file_path_is_under_registry_dir(tmp_path: Path):
    assert daemon.log_file(tmp_path) == tmp_path / "daemon.log"


def test_pid_file_path_is_under_registry_dir(tmp_path: Path):
    assert daemon.pid_file(tmp_path) == tmp_path / "daemon.pid"


@pytest.mark.parametrize("os_name", ["nt", "posix"])
def test_terminate_dispatches_by_platform(monkeypatch, os_name):
    """The Windows/POSIX termination branch is selected by ``os.name`` (spec 0005:
    no Windows CI job exists, so the branch-selection logic is verified here on
    Ubuntu CI via monkeypatch, per the accepted spec's test strategy)."""
    calls: list[str] = []
    monkeypatch.setattr(daemon.os, "name", os_name)
    if os_name == "nt":
        monkeypatch.setattr(
            daemon, "_terminate_windows", lambda pid: calls.append("windows")
        )
    else:
        monkeypatch.setattr(
            daemon, "_terminate_posix", lambda pid: calls.append("posix")
        )

    daemon._terminate(12345)

    assert calls == [os_name if os_name == "posix" else "windows"]
