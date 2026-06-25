"""Tests for ``taskpilot validate`` (task F003-T7, requirement F003-R7,
scenarios F003-S7/S8).
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


def _write_item_missing_title(paths: WorkspacePaths, item_id: str) -> None:
    paths.items_dir.joinpath(f"{item_id}.yaml").write_text(
        f"id: {item_id}\ntype: task\nstatus: backlog\n"
        f"created_at: {NOW}\nupdated_at: {NOW}\n",
        encoding="utf-8",
    )


# --- clean workspace (S7) ----------------------------------------------------


def test_validate_clean_exits_0_with_empty_stderr(workspace):
    item_service.create_item(workspace, title="Valid", type="task", now=NOW)
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    assert "valid" in result.stdout.lower()


def test_validate_empty_workspace_is_clean(workspace):
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert result.stderr == ""


# --- workspace with errors (S8) ----------------------------------------------


def test_validate_reports_errors_to_stderr_and_exits_nonzero(workspace):
    _write_item_missing_title(workspace, "VP-2")
    result = runner.invoke(app, ["validate"])
    assert result.exit_code != 0
    assert "VP-2.yaml" in result.stderr
    assert "title" in result.stderr


# --- JSON mode ---------------------------------------------------------------


def test_validate_json_clean(workspace):
    item_service.create_item(workspace, title="Valid", type="task", now=NOW)
    result = runner.invoke(app, ["--json", "validate"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["summary"]["errors"] == 0


def test_validate_json_with_errors_exits_1(workspace):
    _write_item_missing_title(workspace, "VP-2")
    result = runner.invoke(app, ["--json", "validate"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["summary"]["errors"] >= 1


# --- no workspace ------------------------------------------------------------


def test_validate_without_workspace_exits_1(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1
    assert "No TaskPilot workspace" in result.stderr
