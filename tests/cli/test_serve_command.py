"""Tests for the placeholder ``taskpilot serve`` (task F003-T8, requirement F003-R2).

The real server (F004) is not implemented; the command must fail clearly rather
than pretend to serve, while keeping its --host/--port contract parseable.
"""

from typer.testing import CliRunner

from taskpilot.cli.app import app

runner = CliRunner()


def test_serve_reports_unavailable_and_exits_system_error():
    result = runner.invoke(app, ["serve"])
    assert result.exit_code == 2
    assert "not available" in result.stderr
    assert "F004" in result.stderr


def test_serve_accepts_port_option():
    result = runner.invoke(app, ["serve", "--port", "8080"])
    # Still unavailable, but the option parses (no usage error).
    assert result.exit_code == 2
    assert "not available" in result.stderr


def test_serve_is_listed_in_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "serve" in result.output
