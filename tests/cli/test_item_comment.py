"""Tests for ``taskpilot item comment`` (task F003-T6, requirement F003-R6,
scenario F003-S6).
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from taskpilot.cli.app import app
from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import comment_service, item_service, project_service

runner = CliRunner()
NOW = "2026-06-24T10:00:00Z"


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(paths, key="VP", name="VoicePilot", now=NOW)
    item_service.create_item(paths, title="x", type="task", now=NOW)  # VP-1
    monkeypatch.chdir(tmp_path)
    return paths


def test_comment_creates_file_and_prints_filename(workspace):
    result = runner.invoke(app, ["item", "comment", "VP-1", "Reviewed implementation"])
    assert result.exit_code == 0, result.output
    files = list(workspace.item_comments_dir("VP-1").glob("*.md"))
    assert len(files) == 1
    # stdout prints the created comment filename.
    assert files[0].name in result.output


def test_comment_records_body_and_default_author(workspace):
    runner.invoke(app, ["item", "comment", "VP-1", "Some note"])
    stored = comment_service.list_comments(workspace, "VP-1")
    assert stored[0].body == "Some note"
    assert stored[0].created_by  # non-empty default author


def test_comment_honors_explicit_author(workspace):
    runner.invoke(app, ["item", "comment", "VP-1", "note", "--author", "Aleksei"])
    assert comment_service.list_comments(workspace, "VP-1")[0].created_by == "Aleksei"


def test_comment_json_output(workspace):
    result = runner.invoke(app, ["--json", "item", "comment", "VP-1", "note"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["item_id"] == "VP-1"
    assert payload["filename"].endswith(".md")
    assert payload["path"].startswith(".taskpilot/comments/VP-1/")


def test_comment_on_unknown_item_exits_1(workspace):
    result = runner.invoke(app, ["item", "comment", "VP-404", "note"])
    assert result.exit_code == 1
    assert "Error:" in result.output
