"""Integration tests for ``taskpilot archive`` commands (task TP-110).

Each test runs inside a temp workspace (``monkeypatch.chdir``) so the commands
discover ``.taskpilot/`` from the current directory.
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from taskpilot.cli.app import app
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item, ItemStatus, ItemType, Priority
from taskpilot.core.item_io import write_item
from taskpilot.services import project_service

runner = CliRunner()
NOW = "2026-08-01T00:00:00Z"


def _make_workspace(tmp_path: Path) -> WorkspacePaths:
    """Create a minimal workspace and return its paths."""
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(paths, key="TP", name="TestProject", now=NOW)
    return paths


def _make_old_item(paths: WorkspacePaths, item_id: str, status: ItemStatus) -> Item:
    """Create an item that is 15 days old (past the 14-day default threshold)."""
    item = Item(
        schema_version=1,
        id=item_id,
        title=f"Old {status.value} item",
        type=ItemType.task,
        status=status,
        priority=Priority.normal,
        created_at="2026-07-10T00:00:00Z",
        updated_at="2026-07-20T00:00:00Z",
    )
    return write_item(paths, item)


# --- archive run -----------------------------------------------------------


def test_archive_run_json_empty_when_no_eligible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paths = _make_workspace(tmp_path)
    # Create a recent item (not eligible)
    _make_old_item(paths, "TP-1", ItemStatus.backlog)  # backlog is never eligible
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--json", "archive", "run"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == {"archived": []}


def test_archive_run_archives_eligible_items(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    _make_old_item(paths, "TP-2", ItemStatus.cancelled)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--json", "archive", "run"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert sorted(payload["archived"]) == ["TP-1", "TP-2"]
    # Verify files moved to archived/
    archived_dir = paths.workspace_dir / "archived"
    assert (archived_dir / "2026-08" / "TP-1.yaml").is_file()
    assert (archived_dir / "2026-08" / "TP-2.yaml").is_file()
    assert not paths.item_file("TP-1").exists()
    assert not paths.item_file("TP-2").exists()


def test_archive_run_human_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["archive", "run"])
    assert result.exit_code == 0
    assert "Archived 1 item(s): TP-1" in result.output


def test_archive_run_nothing_to_archive_human(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["archive", "run"])
    assert result.exit_code == 0
    assert "No items eligible for archiving." in result.output


def test_archive_run_skips_already_archived(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    # Archive once
    result1 = runner.invoke(app, ["--json", "archive", "run"])
    assert result1.exit_code == 0
    # Archive again — should be a no-op
    result2 = runner.invoke(app, ["--json", "archive", "run"])
    assert result2.exit_code == 0
    payload = json.loads(result2.output)
    assert payload == {"archived": []}


# --- archive migrate -------------------------------------------------------


def test_archive_migrate_json_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    _make_old_item(paths, "TP-2", ItemStatus.deleted)
    # TP-3 is not eligible (backlog)
    paths2 = WorkspacePaths.for_root(tmp_path)
    _make_old_item(paths2, "TP-3", ItemStatus.backlog)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--json", "archive", "migrate"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["archived_count"] == 2
    assert sorted(payload["archived_ids"]) == ["TP-1", "TP-2"]


def test_archive_migrate_human_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    _make_old_item(paths, "TP-2", ItemStatus.cancelled)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["archive", "migrate"])
    assert result.exit_code == 0
    assert "Archived 2 item(s) via migration." in result.output


def test_archive_migrate_empty_when_none_eligible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--json", "archive", "migrate"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["archived_count"] == 0
    assert payload["archived_ids"] == []


# --- archive unarchive -----------------------------------------------------


def test_archive_unarchive_json_restores_item(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    monkeypatch.chdir(tmp_path)
    # Archive first
    runner.invoke(app, ["--json", "archive", "run"])
    # Unarchive
    result = runner.invoke(app, ["--json", "archive", "unarchive", "TP-1"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["id"] == "TP-1"
    assert payload["status"] == "done"
    # Verify file moved back to items/
    assert paths.item_file("TP-1").is_file()
    archived_dir = paths.workspace_dir / "archived"
    assert not (archived_dir / "2026-08" / "TP-1.yaml").exists()


def test_archive_unarchive_human_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["--json", "archive", "run"])
    result = runner.invoke(app, ["archive", "unarchive", "TP-1"])
    assert result.exit_code == 0
    assert "Unarchived TP-1" in result.output


def test_archive_unarchive_error_on_non_archived(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["archive", "unarchive", "TP-999"])
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_archive_unarchive_rejects_occupied_destination_without_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["archive", "run"]).exit_code == 0
    archived_file = paths.workspace_dir / "archived" / "2026-08" / "TP-1.yaml"
    metadata_file = paths.workspace_dir / "archived" / "2026-08" / "metadata.json"
    archived_before = archived_file.read_bytes()
    metadata_before = metadata_file.read_bytes()
    _make_old_item(paths, "TP-1", ItemStatus.backlog)
    active_before = paths.item_file("TP-1").read_bytes()

    result = runner.invoke(app, ["archive", "unarchive", "TP-1"])

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "already exists" in result.output
    assert paths.item_file("TP-1").read_bytes() == active_before
    assert archived_file.read_bytes() == archived_before
    assert metadata_file.read_bytes() == metadata_before


# --- project archive-threshold ---------------------------------------------


def test_project_archive_threshold_get_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--json", "project", "archive-threshold"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["archive_threshold_days"] == 14


def test_project_archive_threshold_get_human(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["project", "archive-threshold"])
    assert result.exit_code == 0
    assert "archive_threshold_days: 14" in result.output


def test_project_archive_threshold_set_and_get(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["project", "archive-threshold", "--threshold", "30"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["--json", "project", "archive-threshold"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["archive_threshold_days"] == 30


def test_project_archive_threshold_rejects_invalid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["project", "archive-threshold", "--threshold", "0"])
    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "between 1 and 3650" in result.output


def test_project_archive_threshold_rejects_above_max(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["project", "archive-threshold", "--threshold", "9999"])
    assert result.exit_code == 1
    assert "between 1 and 3650" in result.output


def test_project_archive_threshold_accepts_boundary_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["project", "archive-threshold", "--threshold", "1"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["project", "archive-threshold", "--threshold", "3650"])
    assert result.exit_code == 0
