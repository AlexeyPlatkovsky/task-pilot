"""Unit tests for soft item deletion (task F002-T7, requirement F002-R7).

Deletion sets status to "deleted", preserves the file, excludes the item from
default listings while keeping it findable by direct lookup, and is idempotent.
"""

from pathlib import Path

import pytest

from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import item_service, project_service
from taskpilot.services.errors import NotFound


def _workspace(tmp_path: Path) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(paths, key="VP", name="VoicePilot", now="2026-06-20T10:00:00Z")
    return paths


def test_delete_sets_status_and_keeps_file(tmp_path: Path):
    paths = _workspace(tmp_path)
    item = item_service.create_item(paths, title="x", type="task", now="2026-06-20T11:00:00Z")

    deleted = item_service.delete_item(paths, item.id, now="2026-06-21T09:00:00Z")

    assert deleted.status == "deleted"
    assert deleted.updated_at == "2026-06-21T09:00:00Z"
    assert paths.item_file(item.id).is_file()
    # still findable by direct lookup
    assert item_service.read_item(paths, item.id).status == "deleted"


def test_deleted_item_excluded_from_default_list_but_findable(tmp_path: Path):
    paths = _workspace(tmp_path)
    item = item_service.create_item(paths, title="x", type="task")
    item_service.delete_item(paths, item.id)

    assert item.id not in [i.id for i in item_service.list_items(paths)]
    assert item.id in [i.id for i in item_service.list_items(paths, include_deleted=True)]


def test_delete_is_idempotent(tmp_path: Path):
    paths = _workspace(tmp_path)
    item = item_service.create_item(paths, title="x", type="task", now="2026-06-20T11:00:00Z")
    first = item_service.delete_item(paths, item.id, now="2026-06-21T09:00:00Z")
    before = paths.item_file(item.id).read_text(encoding="utf-8")

    second = item_service.delete_item(paths, item.id, now="2026-06-22T09:00:00Z")

    # idempotent: status stays deleted, file not rewritten (updated_at unchanged)
    assert second.status == "deleted"
    assert second.updated_at == first.updated_at
    assert paths.item_file(item.id).read_text(encoding="utf-8") == before


def test_delete_missing_item_raises_not_found(tmp_path: Path):
    paths = _workspace(tmp_path)
    with pytest.raises(NotFound):
        item_service.delete_item(paths, "VP-999")
