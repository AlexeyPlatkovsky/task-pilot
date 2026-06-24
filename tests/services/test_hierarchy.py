"""Unit tests for type-based parent/child hierarchy rules (task F002-T3, F002-R3).

Allowed parent -> child:
  epic    -> feature, task
  feature -> task
  task    -> bug
  bug     -> (none)
"""

from pathlib import Path

import pytest

from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import item_service, project_service
from taskpilot.services.errors import ValidationFailed
from taskpilot.services.hierarchy import ALLOWED_CHILD_TYPES, validate_parent


def _workspace(tmp_path: Path) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(paths, key="VP", name="VoicePilot", now="2026-06-20T10:00:00Z")
    return paths


def test_allowed_table_matches_spec():
    assert ALLOWED_CHILD_TYPES["epic"] == {"feature", "task"}
    assert ALLOWED_CHILD_TYPES["feature"] == {"task"}
    assert ALLOWED_CHILD_TYPES["task"] == {"bug"}
    assert ALLOWED_CHILD_TYPES["bug"] == set()


def test_setting_task_parent_to_feature_succeeds(tmp_path: Path):
    paths = _workspace(tmp_path)
    feature = item_service.create_item(paths, title="feat", type="feature")
    task = item_service.create_item(paths, title="task", type="task")

    updated = item_service.update_item(paths, task.id, parent_id=feature.id)
    assert updated.parent_id == feature.id


def test_setting_bug_parent_to_bug_fails(tmp_path: Path):
    paths = _workspace(tmp_path)
    bug1 = item_service.create_item(paths, title="bug1", type="bug")
    bug2 = item_service.create_item(paths, title="bug2", type="bug")

    with pytest.raises(ValidationFailed):
        item_service.update_item(paths, bug2.id, parent_id=bug1.id)
    # not persisted
    assert item_service.read_item(paths, bug2.id).parent_id is None


def test_bug_cannot_be_child_of_epic(tmp_path: Path):
    paths = _workspace(tmp_path)
    epic = item_service.create_item(paths, title="epic", type="epic")
    bug = item_service.create_item(paths, title="bug", type="bug")

    with pytest.raises(ValidationFailed):
        item_service.update_item(paths, bug.id, parent_id=epic.id)


def test_create_task_with_epic_parent_succeeds(tmp_path: Path):
    paths = _workspace(tmp_path)
    epic = item_service.create_item(paths, title="epic", type="epic")

    task = item_service.create_item(paths, title="task", type="task", parent_id=epic.id)
    assert task.parent_id == epic.id


def test_create_bug_with_epic_parent_fails_without_writing(tmp_path: Path):
    paths = _workspace(tmp_path)
    epic = item_service.create_item(paths, title="epic", type="epic")

    with pytest.raises(ValidationFailed):
        item_service.create_item(paths, title="bug", type="bug", parent_id=epic.id)
    # only the epic exists; the rejected bug was never written
    assert [i.id for i in item_service.list_items(paths)] == [epic.id]


def test_parent_must_exist(tmp_path: Path):
    paths = _workspace(tmp_path)
    task = item_service.create_item(paths, title="task", type="task")
    with pytest.raises(ValidationFailed):
        item_service.update_item(paths, task.id, parent_id="VP-999")


def test_self_parent_rejected(tmp_path: Path):
    paths = _workspace(tmp_path)
    task = item_service.create_item(paths, title="task", type="task")
    with pytest.raises(ValidationFailed):
        item_service.update_item(paths, task.id, parent_id=task.id)


def test_cycle_rejected(tmp_path: Path):
    paths = _workspace(tmp_path)
    epic = item_service.create_item(paths, title="epic", type="epic")
    feature = item_service.create_item(paths, title="feat", type="feature", parent_id=epic.id)
    task = item_service.create_item(paths, title="task", type="task", parent_id=feature.id)
    # making the epic a child of the task would close a cycle epic->feature->task->epic
    with pytest.raises(ValidationFailed):
        item_service.update_item(paths, epic.id, parent_id=task.id)


def test_validate_parent_noop_when_no_parent(tmp_path: Path):
    paths = _workspace(tmp_path)
    # should not raise
    validate_parent(paths, child_id="VP-1", child_type="task", parent_id=None)
