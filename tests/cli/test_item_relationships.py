"""Tests for relationship commands (task F003-T5, requirement F003-R5,
scenario F003-S5): parent/unparent, blocks/unblocks, relates/unrelates.
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from taskpilot.cli.app import app
from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import item_service, link_service, project_service

runner = CliRunner()
NOW = "2026-06-24T10:00:00Z"


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(paths, key="VP", name="VoicePilot", now=NOW)
    monkeypatch.chdir(tmp_path)
    return paths


def _two_tasks(paths):
    item_service.create_item(paths, title="One", type="task", now=NOW)  # VP-1
    item_service.create_item(paths, title="Two", type="task", now=NOW)  # VP-2


# --- blocks / unblocks -------------------------------------------------------


def test_blocks_adds_link_and_is_idempotent(workspace):
    _two_tasks(workspace)
    first = runner.invoke(app, ["item", "blocks", "VP-1", "VP-2"])
    assert first.exit_code == 0, first.output
    assert "VP-1 now blocks VP-2" in first.output
    # Idempotent rerun still succeeds (S5).
    second = runner.invoke(app, ["item", "blocks", "VP-1", "VP-2"])
    assert second.exit_code == 0
    assert link_service.query_links(workspace, "VP-1")["blocks"] == ["VP-2"]


def test_unblocks_removes_link(workspace):
    _two_tasks(workspace)
    link_service.add_link(workspace, "VP-1", "blocks", "VP-2")
    result = runner.invoke(app, ["item", "unblocks", "VP-1", "VP-2"])
    assert result.exit_code == 0
    assert "no longer blocks" in result.output
    assert link_service.query_links(workspace, "VP-1")["blocks"] == []


def test_blocks_unknown_target_exits_1(workspace):
    item_service.create_item(workspace, title="One", type="task", now=NOW)  # VP-1
    result = runner.invoke(app, ["item", "blocks", "VP-1", "VP-404"])
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_blocks_json_returns_source_item(workspace):
    _two_tasks(workspace)
    result = runner.invoke(app, ["--json", "item", "blocks", "VP-1", "VP-2"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["id"] == "VP-1"
    assert payload["links"]["blocks"] == ["VP-2"]


# --- relates / unrelates -----------------------------------------------------


def test_relates_and_unrelates(workspace):
    _two_tasks(workspace)
    add = runner.invoke(app, ["item", "relates", "VP-1", "VP-2"])
    assert add.exit_code == 0 and "now relates to" in add.output
    assert link_service.query_links(workspace, "VP-1")["relates_to"] == ["VP-2"]

    remove = runner.invoke(app, ["item", "unrelates", "VP-1", "VP-2"])
    assert remove.exit_code == 0 and "no longer relates to" in remove.output
    assert link_service.query_links(workspace, "VP-1")["relates_to"] == []


# --- parent / unparent -------------------------------------------------------


def test_parent_sets_and_unparent_clears(workspace):
    item_service.create_item(
        workspace, title="Feature", type="feature", now=NOW
    )  # VP-1
    item_service.create_item(workspace, title="Task", type="task", now=NOW)  # VP-2

    set_result = runner.invoke(app, ["item", "parent", "VP-2", "VP-1"])
    assert set_result.exit_code == 0, set_result.output
    assert "parent set to VP-1" in set_result.output
    assert item_service.read_item(workspace, "VP-2").parent_id == "VP-1"

    clear_result = runner.invoke(app, ["item", "unparent", "VP-2"])
    assert clear_result.exit_code == 0
    assert "parent cleared" in clear_result.output
    assert item_service.read_item(workspace, "VP-2").parent_id is None


def test_parent_invalid_hierarchy_exits_1(workspace):
    # task cannot parent a feature.
    item_service.create_item(workspace, title="Task", type="task", now=NOW)  # VP-1
    item_service.create_item(
        workspace, title="Feature", type="feature", now=NOW
    )  # VP-2
    result = runner.invoke(app, ["item", "parent", "VP-2", "VP-1"])
    assert result.exit_code == 1
    assert "Error:" in result.output
