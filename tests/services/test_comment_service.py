"""Unit tests for the comment service (task F002-T6, requirement F002-R6).

Adding a comment writes a timestamped .md file under comments/<id>/ and does not
modify the item YAML. Listing returns comments chronologically.
"""

from pathlib import Path

import pytest

from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import comment_service, item_service, project_service
from taskpilot.services.errors import NotFound, ValidationFailed


def _workspace(tmp_path: Path) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(paths, key="VP", name="VoicePilot", now="2026-06-20T10:00:00Z")
    return paths


def test_add_comment_writes_file_without_touching_item(tmp_path: Path):
    paths = _workspace(tmp_path)
    item = item_service.create_item(paths, title="x", type="task", now="2026-06-20T10:00:00Z")
    item_yaml_before = paths.item_file(item.id).read_text(encoding="utf-8")

    comment = comment_service.add_comment(
        paths, item.id, body="Investigated parser", created_by="Aleksei", now="2026-06-21T09:00:00Z"
    )

    assert comment.body == "Investigated parser"
    assert comment.created_by == "Aleksei"
    md_files = list(paths.item_comments_dir(item.id).glob("*.md"))
    assert len(md_files) == 1
    # item YAML untouched
    assert paths.item_file(item.id).read_text(encoding="utf-8") == item_yaml_before


def test_comment_filename_encodes_timestamp(tmp_path: Path):
    paths = _workspace(tmp_path)
    item = item_service.create_item(paths, title="x", type="task")
    comment_service.add_comment(paths, item.id, body="b", created_by="A", now="2026-06-21T09:00:00Z")
    names = [p.name for p in paths.item_comments_dir(item.id).glob("*.md")]
    assert names == ["2026-06-21T09-00-00Z.md"]


def test_list_comments_chronological(tmp_path: Path):
    paths = _workspace(tmp_path)
    item = item_service.create_item(paths, title="x", type="task")
    comment_service.add_comment(paths, item.id, body="second", created_by="A", now="2026-06-21T10:00:00Z")
    comment_service.add_comment(paths, item.id, body="first", created_by="A", now="2026-06-20T08:00:00Z")

    bodies = [c.body for c in comment_service.list_comments(paths, item.id)]
    assert bodies == ["first", "second"]


def test_list_comments_empty_when_none(tmp_path: Path):
    paths = _workspace(tmp_path)
    item = item_service.create_item(paths, title="x", type="task")
    assert comment_service.list_comments(paths, item.id) == []


def test_same_second_comments_get_distinct_files(tmp_path: Path):
    paths = _workspace(tmp_path)
    item = item_service.create_item(paths, title="x", type="task")
    comment_service.add_comment(paths, item.id, body="one", created_by="A", now="2026-06-21T09:00:00Z")
    comment_service.add_comment(paths, item.id, body="two", created_by="A", now="2026-06-21T09:00:00Z")
    assert len(list(paths.item_comments_dir(item.id).glob("*.md"))) == 2


def test_add_comment_on_unknown_item_raises_not_found(tmp_path: Path):
    paths = _workspace(tmp_path)
    with pytest.raises(NotFound):
        comment_service.add_comment(paths, "VP-999", body="b", created_by="A")


def test_add_comment_rejects_empty_author(tmp_path: Path):
    paths = _workspace(tmp_path)
    item = item_service.create_item(paths, title="x", type="task")
    with pytest.raises(ValidationFailed):
        comment_service.add_comment(paths, item.id, body="b", created_by="")
