"""Tests for the placeholder ``taskpilot serve`` (task F003-T8, requirement F003-R2).

The real server (F004) is not implemented; the command must fail clearly rather
than pretend to serve, while keeping its --host/--port contract parseable.
"""

from typer.testing import CliRunner

from taskpilot.cli.app import app

runner = CliRunner()


def test_serve_reports_no_workspace_and_exits_system_error():
    result = runner.invoke(app, ["serve"])
    assert result.exit_code == 2
    assert "No TaskPilot workspace" in result.stderr


def test_serve_accepts_port_option():
    result = runner.invoke(app, ["serve", "--port", "8080"])
    assert result.exit_code == 2
    assert "No TaskPilot workspace" in result.stderr


def test_serve_is_listed_in_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "serve" in result.output


def test_serve_default_port_matches_spec():
    # spec 0002: Alpha serve uses port 7152 by default.
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0
    assert "7152" in result.output
