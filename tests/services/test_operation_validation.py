"""Unit tests for centralized pre-write operation validation (task F002-T8, F002-R8).

Operation input is validated and turned into descriptive errors before any file
is written. These tests assert both the standalone validator and that the item
service routes writes through it (no partial files on rejection).
"""

from pathlib import Path

import pytest

from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import item_service, project_service
from taskpilot.services.errors import ValidationFailed
from taskpilot.services.operation_validation import build_validated_item


def _workspace(tmp_path: Path) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(paths, key="VP", name="VoicePilot", now="2026-06-20T10:00:00Z")
    return paths


def _valid_item_data(**overrides) -> dict:
    data = dict(
        id="VP-1", title="t", type="task", priority="normal", status="backlog",
        created_at="2026-06-20T10:00:00Z", updated_at="2026-06-20T10:00:00Z",
    )
    data.update(overrides)
    return data


def test_build_validated_item_accepts_valid_data():
    item = build_validated_item(_valid_item_data())
    assert item.id == "VP-1"


def test_build_validated_item_reports_invalid_enum_descriptively():
    with pytest.raises(ValidationFailed) as exc:
        build_validated_item(_valid_item_data(status="imaginary_status"))
    msg = str(exc.value)
    assert "status" in msg
    assert "imaginary_status" in msg or "expected one of" in msg


def test_build_validated_item_reports_missing_required_field():
    data = _valid_item_data()
    del data["title"]
    with pytest.raises(ValidationFailed) as exc:
        build_validated_item(data)
    assert "title" in str(exc.value)


def test_build_validated_item_reports_bad_timestamp():
    with pytest.raises(ValidationFailed) as exc:
        build_validated_item(_valid_item_data(created_at="not-a-time"))
    assert "created_at" in str(exc.value)


def test_create_item_rejects_invalid_status_and_writes_nothing(tmp_path: Path):
    paths = _workspace(tmp_path)
    with pytest.raises(ValidationFailed):
        item_service.create_item(paths, title="x", type="task", status="imaginary_status")
    assert not any(paths.items_dir.glob("*.yaml"))


def test_update_item_rejects_invalid_value_before_write(tmp_path: Path):
    paths = _workspace(tmp_path)
    created = item_service.create_item(paths, title="x", type="task", now="2026-06-20T11:00:00Z")
    with pytest.raises(ValidationFailed):
        item_service.update_item(paths, created.id, priority="urgent")
    # unchanged on disk
    assert item_service.read_item(paths, created.id).priority == "normal"
