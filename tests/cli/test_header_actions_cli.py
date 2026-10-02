"""CLI tests for ``project unregister`` and ``validate --fix`` (spec 0010 R2.3, R3.5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from taskpilot.cli.app import app
from taskpilot.core.item_io import write_item
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item, ItemLinks, ItemStatus, ItemType, Priority
from taskpilot.services import item_service, project_service, registry, ui_state

runner = CliRunner()
NOW = "2026-01-01T00:00:00Z"


# --- project unregister ------------------------------------------------------


def _seed(home: Path, *ids: str) -> None:
    for pid in ids:
        repo = home.parent / pid
        repo.mkdir(exist_ok=True)
        registry.register_project(
            home, id=pid, key=pid[:2].upper(), name=pid.title(), path=str(repo), now=NOW
        )


def test_project_unregister_removes_entry(tmp_path: Path):
    home = tmp_path / "home"
    _seed(home, "alpha", "beta")
    result = runner.invoke(
        app, ["project", "unregister", "beta"], env={"TASKPILOT_HOME": str(home)}
    )
    assert result.exit_code == 0, result.output
    assert "Unregistered beta" in result.stdout
    assert [e.id for e in registry.list_projects(home)] == ["alpha"]


def test_project_unregister_json_prints_removed_entry(tmp_path: Path):
    home = tmp_path / "home"
    _seed(home, "alpha")
    result = runner.invoke(
        app,
        ["--json", "project", "unregister", "alpha"],
        env={"TASKPILOT_HOME": str(home)},
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["id"] == "alpha"
    assert payload["key"] == "AL"


def test_project_unregister_unknown_exits_1(tmp_path: Path):
    home = tmp_path / "home"
    _seed(home, "alpha")
    result = runner.invoke(
        app, ["project", "unregister", "nope"], env={"TASKPILOT_HOME": str(home)}
    )
    assert result.exit_code == 1
    assert [e.id for e in registry.list_projects(home)] == ["alpha"]


def test_project_unregister_resets_matching_last_opened(tmp_path: Path, monkeypatch):
    home = tmp_path / "home"
    _seed(home, "alpha")
    monkeypatch.setenv("TASKPILOT_HOME", str(home))
    ui_state.save_ui_state(ui_state.UIState(last_opened_project_id="alpha"))
    result = runner.invoke(app, ["project", "unregister", "alpha"])
    assert result.exit_code == 0, result.output
    assert ui_state.load_ui_state().last_opened_project_id is None


# --- validate --fix ----------------------------------------------------------


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(paths, key="VP", name="VoicePilot", now=NOW)
    monkeypatch.chdir(tmp_path)
    return paths


def _dangling(paths: WorkspacePaths) -> None:
    write_item(
        paths,
        Item(
            schema_version=1,
            id="VP-1",
            title="Has dangling link",
            type=ItemType.task,
            status=ItemStatus.backlog,
            priority=Priority.normal,
            created_at=NOW,
            updated_at=NOW,
            links=ItemLinks(blocks=["VP-99"], relates_to=[]),
        ),
    )


def test_validate_without_fix_keeps_exit_code_and_hints(workspace):
    _dangling(workspace)
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1
    assert "1 issue(s) can be fixed automatically: run taskpilot validate --fix" in (
        result.stderr
    )
    item = item_service.read_item(workspace, "VP-1")
    assert item.links is not None and item.links.blocks == ["VP-99"]


def test_validate_without_fix_json_is_unchanged_shape(workspace):
    _dangling(workspace)
    result = runner.invoke(app, ["--json", "validate"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert "applied" not in payload
    assert "--fix" not in result.stderr
    assert "findings" in payload


def test_validate_clean_has_no_hint(workspace):
    item_service.create_item(workspace, title="Valid", type="task", now=NOW)
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert result.stderr == ""


def test_validate_fix_applies_and_exits_0(workspace):
    _dangling(workspace)
    result = runner.invoke(app, ["validate", "--fix"])
    assert result.exit_code == 0, result.output
    assert "Remove links.blocks -> VP-99 from VP-1" in result.stdout
    item = item_service.read_item(workspace, "VP-1")
    assert item.links is None or item.links.blocks == []


def test_validate_fix_json_reports_applied_and_report(workspace):
    _dangling(workspace)
    result = runner.invoke(app, ["--json", "validate", "--fix"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert [f["kind"] for f in payload["applied"]] == ["remove_link"]
    assert payload["failed"] == []
    assert payload["report"]["ok"] is True


def test_validate_fix_exits_1_when_unfixable_errors_remain(workspace):
    _dangling(workspace)
    bad = workspace.items_dir / "VP-5.yaml"
    bad.write_text("id: [unclosed\n", encoding="utf-8")

    result = runner.invoke(app, ["validate", "--fix"])

    assert result.exit_code == 1
    assert "Remove links.blocks -> VP-99 from VP-1" in result.stdout
    assert "VP-5.yaml" in result.stderr
    assert bad.read_text(encoding="utf-8") == "id: [unclosed\n"
