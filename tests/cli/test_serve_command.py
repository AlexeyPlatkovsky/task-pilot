"""Tests for ``taskpilot serve`` (task F005-T6, requirement F005-R6).

The command must fail clearly when no workspace is found or when the supplied
workspace path is not fully initialized (missing project.yaml), while keeping
its --host/--port/--workspace options parseable.
"""

from pathlib import Path

from typer.testing import CliRunner

from taskpilot.cli.app import app

runner = CliRunner()


def test_serve_reports_no_workspace_and_exits_user_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["serve"])
    assert result.exit_code == 1
    assert "No TaskPilot workspace" in result.stderr


def test_serve_accepts_port_option(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["serve", "--port", "8080"])
    assert result.exit_code == 1
    assert "No TaskPilot workspace" in result.stderr


def test_serve_is_listed_in_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "serve" in result.output


def test_serve_default_port_matches_spec():
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0
    assert "7152" in result.output


def test_serve_workspace_missing_dot_taskpilot(tmp_path: Path):
    result = runner.invoke(app, ["serve", "--workspace", str(tmp_path)])
    assert result.exit_code == 1
    assert "Error:" in result.stderr


def test_serve_workspace_missing_project_yaml(tmp_path: Path):
    (tmp_path / ".taskpilot").mkdir()
    result = runner.invoke(app, ["serve", "--workspace", str(tmp_path)])
    assert result.exit_code == 1
    assert "project.yaml" in result.stderr


def test_serve_workspace_nonexistent_path(tmp_path: Path):
    result = runner.invoke(app, ["serve", "--workspace", str(tmp_path / "ghost")])
    assert result.exit_code == 1
    assert "Error:" in result.stderr


def test_serve_autodetect_missing_project_yaml(tmp_path: Path, monkeypatch):
    (tmp_path / ".taskpilot").mkdir()
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["serve"])
    assert result.exit_code == 1
    assert "project.yaml" in result.stderr
