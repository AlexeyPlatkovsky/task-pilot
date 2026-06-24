"""Unit tests for the item service (task F002-T2, requirement F002-R2).

Covers create with id allocation, read by id, field update with updated_at
refresh, and filtered listing (project/status/type, deleted excluded by default).
"""

from pathlib import Path

import pytest

from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item
from taskpilot.services import item_service, project_service
from taskpilot.services.errors import NotFound, ValidationFailed


def _workspace(tmp_path: Path) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(paths, key="VP", name="VoicePilot", now="2026-06-20T10:00:00Z")
    return paths


def test_create_item_allocates_sequential_id_with_project_key(tmp_path: Path):
    paths = _workspace(tmp_path)

    first = item_service.create_item(paths, title="Add benchmark", type="task")
    second = item_service.create_item(paths, title="Second", type="task")

    assert first.id == "VP-1"
    assert second.id == "VP-2"
    assert paths.item_file("VP-1").is_file()


def test_create_item_persists_and_reads_back_fields(tmp_path: Path):
    paths = _workspace(tmp_path)

    created = item_service.create_item(
        paths, title="Add benchmark", type="task", priority="normal", now="2026-06-20T11:00:00Z"
    )

    read = item_service.read_item(paths, created.id)
    assert read.title == "Add benchmark"
    assert read.type == "task"
    assert read.priority == "normal"
    assert read.status == "backlog"  # default workflow status on create
    assert read.created_at == "2026-06-20T11:00:00Z"
    assert read.updated_at == "2026-06-20T11:00:00Z"


def test_create_item_rejects_invalid_status_without_writing(tmp_path: Path):
    paths = _workspace(tmp_path)

    with pytest.raises(ValidationFailed):
        item_service.create_item(paths, title="Bad", type="task", status="imaginary_status")

    assert not any(paths.items_dir.glob("*.yaml"))


def test_create_item_requires_existing_project(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)  # not initialized
    with pytest.raises(NotFound):
        item_service.create_item(paths, title="X", type="task")


def test_next_id_skips_gaps_from_deleted_items(tmp_path: Path):
    paths = _workspace(tmp_path)
    item_service.create_item(paths, title="one", type="task")  # VP-1
    item_service.create_item(paths, title="two", type="task")  # VP-2
    paths.item_file("VP-1").unlink()  # simulate a gap

    third = item_service.create_item(paths, title="three", type="task")
    assert third.id == "VP-3"  # max+1, gap not reused


def test_update_item_changes_status_and_refreshes_updated_at(tmp_path: Path):
    paths = _workspace(tmp_path)
    created = item_service.create_item(paths, title="Add benchmark", type="task", now="2026-06-20T11:00:00Z")

    updated = item_service.update_item(
        paths, created.id, now="2026-06-21T09:00:00Z", status="in_progress"
    )

    assert updated.status == "in_progress"
    assert updated.updated_at == "2026-06-21T09:00:00Z"
    assert updated.created_at == "2026-06-20T11:00:00Z"
    assert updated.updated_at > updated.created_at
    # persisted
    assert item_service.read_item(paths, created.id).status == "in_progress"


def test_update_item_rejects_invalid_value_and_preserves_file(tmp_path: Path):
    paths = _workspace(tmp_path)
    created = item_service.create_item(paths, title="Add benchmark", type="task", now="2026-06-20T11:00:00Z")

    with pytest.raises(ValidationFailed):
        item_service.update_item(paths, created.id, status="imaginary_status")

    assert item_service.read_item(paths, created.id).status == "backlog"


def test_update_item_missing_returns_not_found(tmp_path: Path):
    paths = _workspace(tmp_path)
    with pytest.raises(NotFound):
        item_service.update_item(paths, "VP-999", status="done")


def test_read_item_missing_returns_not_found(tmp_path: Path):
    paths = _workspace(tmp_path)
    with pytest.raises(NotFound):
        item_service.read_item(paths, "VP-1")


def test_list_items_excludes_deleted_by_default(tmp_path: Path):
    paths = _workspace(tmp_path)
    keep = item_service.create_item(paths, title="keep", type="task")
    gone = item_service.create_item(paths, title="gone", type="task")
    item_service.update_item(paths, gone.id, status="deleted")

    listed = item_service.list_items(paths)
    ids = [i.id for i in listed]
    assert keep.id in ids
    assert gone.id not in ids

    with_deleted = item_service.list_items(paths, include_deleted=True)
    assert gone.id in [i.id for i in with_deleted]


def test_list_items_filters_by_status_and_type(tmp_path: Path):
    paths = _workspace(tmp_path)
    a = item_service.create_item(paths, title="a", type="task")
    item_service.create_item(paths, title="b", type="bug")
    item_service.update_item(paths, a.id, status="in_progress")

    in_progress = item_service.list_items(paths, status="in_progress")
    assert [i.id for i in in_progress] == [a.id]

    bugs = item_service.list_items(paths, type="bug")
    assert [i.type for i in bugs] == ["bug"]


def test_list_items_filters_by_project_key_prefix(tmp_path: Path):
    paths = _workspace(tmp_path)
    item_service.create_item(paths, title="a", type="task")
    # an item from a different project key sitting in the same workspace
    other = Item(
        id="OT-1", title="other", type="task", status="backlog",
        created_at="2026-06-20T10:00:00Z", updated_at="2026-06-20T10:00:00Z",
    )
    from taskpilot.core.item_io import write_item
    write_item(paths, other)

    vp = item_service.list_items(paths, project="VP")
    assert all(i.id.startswith("VP-") for i in vp)
    assert "OT-1" not in [i.id for i in vp]


def test_list_items_sorted_by_numeric_id(tmp_path: Path):
    paths = _workspace(tmp_path)
    for _ in range(11):
        item_service.create_item(paths, title="x", type="task")
    ids = [i.id for i in item_service.list_items(paths)]
    assert ids[:3] == ["VP-1", "VP-2", "VP-3"]
    assert ids[-1] == "VP-11"  # numeric, not lexical
