"""Contract tests: CLI command output shapes, exit codes, error messages (task TP-110).

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


# --- archive run contract --------------------------------------------------


def test_archive_run_json_output_shape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--json", "archive", "run"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert isinstance(payload, dict)
    assert "archived" in payload
    assert isinstance(payload["archived"], list)
    assert "TP-1" in payload["archived"]


def test_archive_run_text_output_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    _make_old_item(paths, "TP-2", ItemStatus.cancelled)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["archive", "run"])
    assert result.exit_code == 0
    assert "Archived 2 item(s):" in result.output
    assert "TP-1" in result.output
    assert "TP-2" in result.output


def test_archive_run_json_empty_is_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--json", "archive", "run"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == {"archived": []}


# --- archive migrate contract ----------------------------------------------


def test_archive_migrate_json_output_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    _make_old_item(paths, "TP-2", ItemStatus.deleted)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--json", "archive", "migrate"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert isinstance(payload, dict)
    assert "archived_count" in payload
    assert "archived_ids" in payload
    assert isinstance(payload["archived_count"], int)
    assert payload["archived_count"] == 2
    assert isinstance(payload["archived_ids"], list)
    assert sorted(payload["archived_ids"]) == ["TP-1", "TP-2"]


def test_archive_migrate_text_output_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paths = _make_workspace(tmp_path)
    _make_old_item(paths, "TP-1", ItemStatus.done)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["archive", "migrate"])
    assert result.exit_code == 0
    assert "Archived 1 item(s) via migration." in result.output


def test_archive_migrate_json_empty_is_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--json", "archive", "migrate"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["archived_count"] == 0
    assert payload["archived_ids"] == []


# --- archive unarchive contract --------------------------------------------


def test_archive_migrate_storage_json_output_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paths = _make_workspace(tmp_path)
    root = paths.workspace_dir / "archived"
    root.mkdir()
    _make_old_item(paths, "TP-1", ItemStatus.done)
    _make_old_item(paths, "TP-2", ItemStatus.done)
    root_file = root / "TP-1.yaml"
    paths.item_file("TP-1").replace(root_file)
    paths.item_file("TP-2").replace(root / "TP-2.yaml")
    (root / "metadata.json").write_text(
        json.dumps(
            {
                "TP-2": {
                    "original_id": "TP-2",
                    "project_key": "TP",
                    "archived_at": "2026-07-15T10:00:00Z",
                    "original_status": "done",
                },
                "TP-1": {
                    "original_id": "TP-1",
                    "project_key": "TP",
                    "archived_at": "2026-06-15T10:00:00Z",
                    "original_status": "done",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["--json", "archive", "migrate-storage"])

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "migrated_count": 2,
        "migrated_ids": ["TP-1", "TP-2"],
    }
    assert (root / "2026-06" / "TP-1.yaml").is_file()
    assert (root / "2026-07" / "TP-2.yaml").is_file()


def test_archive_unarchive_json_output_shape(
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
    assert isinstance(payload, dict)
    assert payload["id"] == "TP-1"
    assert payload["status"] == "done"


def test_archive_unarchive_text_output_format(
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


# --- project archive-threshold contract ------------------------------------


def test_project_archive_threshold_get_json_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--json", "project", "archive-threshold"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert isinstance(payload, dict)
    assert "archive_threshold_days" in payload
    assert isinstance(payload["archive_threshold_days"], int)
    assert payload["archive_threshold_days"] == 14


def test_project_archive_threshold_get_text_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["project", "archive-threshold"])
    assert result.exit_code == 0
    assert "archive_threshold_days: 14" in result.output


def test_project_archive_threshold_set_json_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["--json", "project", "archive-threshold", "--threshold", "21"]
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["archive_threshold_days"] == 21


def test_project_archive_threshold_set_text_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["project", "archive-threshold", "--threshold", "7"])
    assert result.exit_code == 0
    assert "archive_threshold_days: 7" in result.output


def test_project_archive_threshold_error_on_invalid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["project", "archive-threshold", "--threshold", "0"])
    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "between 1 and 3650" in result.output


def test_project_archive_threshold_error_on_above_max(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _make_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["project", "archive-threshold", "--threshold", "9999"])
    assert result.exit_code == 1
    assert "between 1 and 3650" in result.output
