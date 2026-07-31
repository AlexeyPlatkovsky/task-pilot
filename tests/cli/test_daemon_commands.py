"""Tests for ``taskpilot start/stop/restart/status/logs`` (task TP-122, spec
docs/specs/0005-daemon-lifecycle-commands.md).

Isolated from the real home directory via ``TASKPILOT_HOME`` (the existing seam
used by ``services/registry.py`` and ``tests/server/test_api.py``). ``start`` is
exercised as a real short-lived subprocess rather than a mocked spawn, per the
accepted spec's test strategy, so the detach behavior is genuinely covered.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from typer.testing import CliRunner

from taskpilot.cli.app import app
from taskpilot.services import daemon

runner = CliRunner()


def _wait_for_pid_file(registry_dir: Path, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if daemon.pid_file(registry_dir).exists():
            return
        time.sleep(0.05)
    raise AssertionError("daemon.pid was never written")


def test_status_reports_not_running_when_no_daemon(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TASKPILOT_HOME", str(tmp_path))
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "not running" in result.output.lower()


def test_stop_reports_not_running_and_exits_nonzero(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TASKPILOT_HOME", str(tmp_path))
    result = runner.invoke(app, ["stop"])
    assert result.exit_code == 1
    assert "not running" in (result.output + result.stderr).lower()


def test_logs_reports_missing_log_file(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TASKPILOT_HOME", str(tmp_path))
    result = runner.invoke(app, ["logs"])
    assert result.exit_code == 1
    assert "log" in (result.output + result.stderr).lower()


def test_start_status_stop_lifecycle_with_real_subprocess(tmp_path: Path, monkeypatch):
    """Real end-to-end lifecycle: spawn a genuine detached child, observe it via
    ``status``, then tear it down via ``stop`` — no mocked process spawn."""
    monkeypatch.setenv("TASKPILOT_HOME", str(tmp_path))
    monkeypatch.setattr(
        "taskpilot.cli.commands.daemon._SERVER_COMMAND",
        [sys.executable, "-c", "import time; time.sleep(60)"],
    )

    try:
        start_result = runner.invoke(app, ["start"])
        assert start_result.exit_code == 0

        registry_dir = tmp_path
        _wait_for_pid_file(registry_dir)
        state = daemon.read_state(registry_dir)
        assert state is not None

        status_result = runner.invoke(app, ["status"])
        assert status_result.exit_code == 0
        assert str(state.pid) in status_result.output

        second_start = runner.invoke(app, ["start"])
        assert second_start.exit_code == 1
        assert str(state.pid) in (second_start.output + second_start.stderr)
    finally:
        stop_result = runner.invoke(app, ["stop"])
        # Either it stopped cleanly here, or the fixture-level daemon was
        # already torn down by an assertion above — both leave nothing running.
        assert stop_result.exit_code in (0, 1)

    final_status = runner.invoke(app, ["status"])
    assert final_status.exit_code == 0
    assert "not running" in final_status.output.lower()


def test_restart_stops_existing_and_starts_new(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TASKPILOT_HOME", str(tmp_path))
    monkeypatch.setattr(
        "taskpilot.cli.commands.daemon._SERVER_COMMAND",
        [sys.executable, "-c", "import time; time.sleep(60)"],
    )

    try:
        runner.invoke(app, ["start"])
        _wait_for_pid_file(tmp_path)
        first_state = daemon.read_state(tmp_path)
        assert first_state is not None

        restart_result = runner.invoke(app, ["restart"])
        assert restart_result.exit_code == 0

        _wait_for_pid_file(tmp_path)
        second_state = daemon.read_state(tmp_path)
        assert second_state is not None
        assert second_state.pid != first_state.pid
    finally:
        runner.invoke(app, ["stop"])


def test_start_is_listed_in_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("start", "stop", "restart", "status", "logs"):
        assert name in result.output


def test_status_json_reports_not_running_as_valid_json(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TASKPILOT_HOME", str(tmp_path))
    result = runner.invoke(app, ["--json", "status"])
    assert result.exit_code == 0
    assert json.loads(result.output) == {"running": False}


def test_status_json_reports_running_as_valid_json(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TASKPILOT_HOME", str(tmp_path))
    monkeypatch.setattr(
        "taskpilot.cli.commands.daemon._SERVER_COMMAND",
        [sys.executable, "-c", "import time; time.sleep(60)"],
    )
    try:
        runner.invoke(app, ["start"])
        _wait_for_pid_file(tmp_path)
        state = daemon.read_state(tmp_path)
        assert state is not None

        result = runner.invoke(app, ["--json", "status"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload == {
            "running": True,
            "pid": state.pid,
            "host": state.host,
            "port": state.port,
            "started_at": state.started_at,
        }
    finally:
        runner.invoke(app, ["stop"])


def test_restart_reports_clean_error_when_start_daemon_conflicts(
    tmp_path: Path, monkeypatch
):
    """Between ``stop_daemon`` releasing the lock and ``start_daemon``
    re-acquiring it, a concurrent ``taskpilot start`` could win — ``restart``
    must report that as a formatted user error, not an unhandled traceback.
    Forcing ``start_daemon`` to raise ``ConflictError`` exercises that handler
    deterministically without needing an actual concurrent process."""
    monkeypatch.setenv("TASKPILOT_HOME", str(tmp_path))

    from taskpilot.services.errors import ConflictError

    def _always_conflicts(*args, **kwargs):
        raise ConflictError("Daemon already running (pid 999, http://127.0.0.1:7152)")

    monkeypatch.setattr(
        "taskpilot.cli.commands.daemon.daemon.start_daemon", _always_conflicts
    )

    result = runner.invoke(app, ["restart"])

    assert result.exit_code == 1
    assert "Error:" in (result.output + result.stderr)
    assert "already running" in (result.output + result.stderr).lower()
