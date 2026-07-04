"""Tests for ``taskpilot serve`` (task F005-T6, requirement F005-R6).

The command starts the local WebUI/API from any directory by using the machine
registry. An explicit ``--workspace`` remains a strict validation request for a
specific initialized workspace.
"""

from pathlib import Path

from typer.testing import CliRunner

from taskpilot.cli.app import app

runner = CliRunner()


def test_serve_starts_without_workspace_from_any_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls: list[dict[str, object]] = []

    def fake_run(app_factory, *, factory, host, port):
        calls.append(
            {
                "app_factory": app_factory,
                "factory": factory,
                "host": host,
                "port": port,
            }
        )

    monkeypatch.setattr("taskpilot.cli.commands.serve.uvicorn.run", fake_run)

    result = runner.invoke(app, ["serve"])
    assert result.exit_code == 0
    assert "TaskPilot server starting on http://127.0.0.1:7152" in result.output
    assert calls == [
        {
            "app_factory": "taskpilot.server.app:create_app_from_env",
            "factory": True,
            "host": "127.0.0.1",
            "port": 7152,
        }
    ]


def test_serve_accepts_port_option(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls: list[dict[str, object]] = []

    def fake_run(app_factory, *, factory, host, port):
        calls.append(
            {
                "app_factory": app_factory,
                "factory": factory,
                "host": host,
                "port": port,
            }
        )

    monkeypatch.setattr("taskpilot.cli.commands.serve.uvicorn.run", fake_run)

    result = runner.invoke(app, ["serve", "--port", "8080"])
    assert result.exit_code == 0
    assert "http://127.0.0.1:8080" in result.output
    assert calls[0]["port"] == 8080


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


def test_serve_ignores_incomplete_workspace_in_current_directory(
    tmp_path: Path, monkeypatch
):
    (tmp_path / ".taskpilot").mkdir()
    monkeypatch.chdir(tmp_path)
    calls: list[dict[str, object]] = []

    def fake_run(app_factory, *, factory, host, port):
        calls.append(
            {
                "app_factory": app_factory,
                "factory": factory,
                "host": host,
                "port": port,
            }
        )

    monkeypatch.setattr("taskpilot.cli.commands.serve.uvicorn.run", fake_run)

    result = runner.invoke(app, ["serve"])
    assert result.exit_code == 0
    assert calls[0]["port"] == 7152


def test_serve_module_does_not_import_server_adapter():
    """The CLI serve command must not statically import the REST API adapter (F-2 / TP-4).

    Launching the server happens via uvicorn's import-string + env factory, so the
    cli->server adapter-to-adapter import is removed at the source level.
    """
    import inspect

    from taskpilot.cli.commands import serve as serve_module

    source = inspect.getsource(serve_module)
    assert "from taskpilot.server" not in source
    assert "import taskpilot.server" not in source
