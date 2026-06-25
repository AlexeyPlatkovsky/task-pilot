"""Tests for ``taskpilot item`` list/show/create/update (task F003-T4,
requirement F003-R4, scenarios F003-S3/S4).

Each test runs inside a temp workspace (``monkeypatch.chdir``) so the commands
discover ``.taskpilot/`` from the current directory.
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from taskpilot.cli.app import app
from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import item_service, project_service

runner = CliRunner()
NOW = "2026-06-24T10:00:00Z"


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(paths, key="VP", name="VoicePilot", now=NOW)
    monkeypatch.chdir(tmp_path)
    return paths


# --- create ------------------------------------------------------------------


def test_create_prints_id_and_writes_file(workspace):
    result = runner.invoke(
        app, ["item", "create", "--title", "Benchmark task", "--type", "task"]
    )
    assert result.exit_code == 0, result.output
    assert "VP-1" in result.output
    assert workspace.item_file("VP-1").is_file()


def test_create_json_outputs_item(workspace):
    result = runner.invoke(
        app,
        [
            "--json",
            "item",
            "create",
            "--title",
            "Task",
            "--type",
            "task",
            "--priority",
            "high",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["id"] == "VP-1"
    assert payload["priority"] == "high"


def test_create_invalid_type_exits_1(workspace):
    result = runner.invoke(app, ["item", "create", "--title", "X", "--type", "nope"])
    assert result.exit_code == 1
    assert "Error:" in result.output
    # No file written on invalid input.
    assert not workspace.item_file("VP-1").exists()


def test_create_missing_required_field_is_usage_error(workspace):
    result = runner.invoke(app, ["item", "create", "--type", "task"])
    assert result.exit_code != 0
    assert result.exit_code != 1  # Typer usage error, not a domain error


# --- show --------------------------------------------------------------------


def test_show_json_is_deterministic(workspace):
    item_service.create_item(workspace, title="Benchmark task", type="task", now=NOW)
    first = runner.invoke(app, ["--json", "item", "show", "VP-1"])
    second = runner.invoke(app, ["--json", "item", "show", "VP-1"])
    assert first.exit_code == 0, first.output
    assert first.output == second.output
    payload = json.loads(first.output)
    assert payload["id"] == "VP-1"
    assert payload["title"] == "Benchmark task"


def test_show_human_key_values(workspace):
    item_service.create_item(workspace, title="Benchmark task", type="task", now=NOW)
    result = runner.invoke(app, ["item", "show", "VP-1"])
    assert result.exit_code == 0
    assert "VP-1" in result.output and "Benchmark task" in result.output


def test_show_unknown_item_exits_1(workspace):
    result = runner.invoke(app, ["item", "show", "VP-404"])
    assert result.exit_code == 1
    assert "Error:" in result.output


# --- list --------------------------------------------------------------------


def test_list_json_returns_created_items(workspace):
    item_service.create_item(workspace, title="A", type="task", now=NOW)
    item_service.create_item(workspace, title="B", type="bug", now=NOW)
    result = runner.invoke(app, ["--json", "item", "list"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert [i["id"] for i in payload] == ["VP-1", "VP-2"]


def test_list_filters_by_status(workspace):
    item_service.create_item(workspace, title="A", type="task", status="done", now=NOW)
    item_service.create_item(
        workspace, title="B", type="task", status="backlog", now=NOW
    )
    result = runner.invoke(app, ["--json", "item", "list", "--status", "done"])
    payload = json.loads(result.output)
    assert [i["id"] for i in payload] == ["VP-1"]


def test_list_empty_human(workspace):
    result = runner.invoke(app, ["item", "list"])
    assert result.exit_code == 0
    assert "No items found" in result.output


# --- update ------------------------------------------------------------------


def test_update_changes_field(workspace):
    item_service.create_item(workspace, title="Old", type="task", now=NOW)
    result = runner.invoke(
        app, ["item", "update", "VP-1", "--title", "New", "--status", "ready"]
    )
    assert result.exit_code == 0, result.output
    assert "Updated VP-1" in result.output
    assert item_service.read_item(workspace, "VP-1").title == "New"


def test_update_unknown_item_exits_1(workspace):
    result = runner.invoke(app, ["item", "update", "VP-404", "--title", "X"])
    assert result.exit_code == 1
    assert "Error:" in result.output


# --- no workspace ------------------------------------------------------------


def test_commands_without_workspace_exit_1(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["item", "list"])
    assert result.exit_code == 1
    assert "No TaskPilot workspace" in result.output
