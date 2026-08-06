"""Regression coverage for TP-134 archive-month storage and legacy migration."""

from __future__ import annotations

import json
import os
from pathlib import Path

from taskpilot.core.item_io import write_item
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item, ItemStatus, ItemType, Priority
from taskpilot.services import archive_service, project_service


def _paths(tmp_path: Path) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(
        paths, key="TP", name="Test project", now="2026-01-01T00:00:00Z"
    )
    return paths


def _item(paths: WorkspacePaths, item_id: str) -> Item:
    return write_item(
        paths,
        Item(
            schema_version=1,
            id=item_id,
            title=item_id,
            type=ItemType.task,
            status=ItemStatus.done,
            priority=Priority.normal,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
        ),
    )


def test_archive_uses_archived_at_month_for_yaml_and_metadata(tmp_path: Path):
    paths = _paths(tmp_path)
    _item(paths, "TP-1")

    assert archive_service.archive_items(
        paths, ["TP-1"], now="2026-06-30T23:59:59Z"
    ) == ["TP-1"]

    month = paths.workspace_dir / "archived" / "2026-06"
    assert (month / "TP-1.yaml").is_file()
    metadata = json.loads((month / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["TP-1"]["archived_at"] == "2026-06-30T23:59:59Z"
    assert not (paths.workspace_dir / "archived" / "TP-1.yaml").exists()
    assert not (paths.workspace_dir / "archived" / "metadata.json").exists()


def test_listing_and_id_reservation_aggregate_months_and_legacy_in_id_order(
    tmp_path: Path,
):
    paths = _paths(tmp_path)
    _item(paths, "TP-2")
    _item(paths, "TP-1")

    archive_service.archive_items(paths, ["TP-2"], now="2026-06-01T00:00:00Z")
    archive_service.archive_items(paths, ["TP-1"], now="2026-07-01T00:00:00Z")

    _item(paths, "TP-3")
    root = paths.workspace_dir / "archived"
    os.replace(paths.item_file("TP-3"), root / "TP-3.yaml")
    (root / "metadata.json").write_text(
        json.dumps(
            {
                "TP-3": {
                    "original_id": "TP-3",
                    "project_key": "TP",
                    "archived_at": "2026-05-01T00:00:00Z",
                    "original_status": "done",
                }
            }
        ),
        encoding="utf-8",
    )

    assert archive_service.archived_item_ids(paths) == ["TP-1", "TP-2", "TP-3"]
    assert [item.id for item in archive_service.list_archived_items(paths)] == [
        "TP-1",
        "TP-2",
        "TP-3",
    ]


def test_archive_month_partition_handles_utc_year_boundary(tmp_path: Path):
    paths = _paths(tmp_path)
    _item(paths, "TP-1")
    _item(paths, "TP-2")

    archive_service.archive_items(paths, ["TP-1"], now="2026-12-31T23:59:59Z")
    archive_service.archive_items(paths, ["TP-2"], now="2027-01-01T00:00:00Z")

    root = paths.workspace_dir / "archived"
    assert (root / "2026-12" / "TP-1.yaml").is_file()
    assert (root / "2027-01" / "TP-2.yaml").is_file()


def test_legacy_root_archive_is_readable_and_unarchivable(tmp_path: Path):
    paths = _paths(tmp_path)
    _item(paths, "TP-1")
    root = paths.workspace_dir / "archived"
    root.mkdir(parents=True)
    os.replace(paths.item_file("TP-1"), root / "TP-1.yaml")
    (root / "metadata.json").write_text(
        json.dumps(
            {
                "TP-1": {
                    "original_id": "TP-1",
                    "project_key": "TP",
                    "archived_at": "2026-06-15T10:00:00Z",
                    "original_status": "done",
                }
            }
        ),
        encoding="utf-8",
    )

    assert archive_service.archived_item_ids(paths) == ["TP-1"]
    assert [item.id for item in archive_service.list_archived_items(paths)] == ["TP-1"]
    assert archive_service.unarchive_item(paths, "TP-1").id == "TP-1"
    assert paths.item_file("TP-1").is_file()
    assert not (root / "TP-1.yaml").exists()
    assert not (root / "metadata.json").exists()


def test_migrate_legacy_archives_preserves_bytes_and_is_idempotent(tmp_path: Path):
    paths = _paths(tmp_path)
    _item(paths, "TP-1")
    _item(paths, "TP-2")
    root = paths.workspace_dir / "archived"
    root.mkdir(parents=True)
    os.replace(paths.item_file("TP-1"), root / "TP-1.yaml")
    os.replace(paths.item_file("TP-2"), root / "TP-2.yaml")
    original = (root / "TP-1.yaml").read_bytes()
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
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (root / ".archived.lock").write_bytes(b"lock")

    assert archive_service.migrate_legacy_archives(paths) == ["TP-1", "TP-2"]
    migrated = root / "2026-06" / "TP-1.yaml"
    assert migrated.read_bytes() == original
    assert (root / "2026-07" / "TP-2.yaml").is_file()
    assert not (root / "TP-1.yaml").exists()
    assert not (root / "metadata.json").exists()
    assert (root / ".archived.lock").read_bytes() == b"lock"
    assert archive_service.migrate_legacy_archives(paths) == []
    assert archive_service.unarchive_item(paths, "TP-1").id == "TP-1"


def test_migrate_legacy_archives_retries_after_file_and_metadata_publication(
    tmp_path: Path,
):
    paths = _paths(tmp_path)
    _item(paths, "TP-1")
    root = paths.workspace_dir / "archived"
    root.mkdir(parents=True)
    os.replace(paths.item_file("TP-1"), root / "TP-1.yaml")
    entry = {
        "original_id": "TP-1",
        "project_key": "TP",
        "archived_at": "2026-06-15T10:00:00Z",
        "original_status": "done",
    }
    original = (root / "TP-1.yaml").read_bytes()
    (root / "metadata.json").write_text(json.dumps({"TP-1": entry}), encoding="utf-8")
    month = root / "2026-06"
    month.mkdir()
    os.replace(root / "TP-1.yaml", month / "TP-1.yaml")
    (month / "metadata.json").write_text(json.dumps({"TP-1": entry}), encoding="utf-8")

    assert archive_service.migrate_legacy_archives(paths) == ["TP-1"]
    assert (month / "TP-1.yaml").read_bytes() == original
    assert json.loads((month / "metadata.json").read_text()) == {"TP-1": entry}
    assert not (root / "metadata.json").exists()
    assert archive_service.migrate_legacy_archives(paths) == []


def test_migrate_legacy_archives_retries_after_yaml_move_before_metadata(
    tmp_path: Path,
):
    paths = _paths(tmp_path)
    _item(paths, "TP-1")
    root = paths.workspace_dir / "archived"
    root.mkdir(parents=True)
    os.replace(paths.item_file("TP-1"), root / "TP-1.yaml")
    entry = {
        "original_id": "TP-1",
        "project_key": "TP",
        "archived_at": "2026-06-15T10:00:00Z",
        "original_status": "done",
    }
    original = (root / "TP-1.yaml").read_bytes()
    (root / "metadata.json").write_text(json.dumps({"TP-1": entry}), encoding="utf-8")
    month = root / "2026-06"
    month.mkdir()
    os.replace(root / "TP-1.yaml", month / "TP-1.yaml")

    assert archive_service.migrate_legacy_archives(paths) == ["TP-1"]
    assert (month / "TP-1.yaml").read_bytes() == original
    assert json.loads((month / "metadata.json").read_text()) == {"TP-1": entry}
    assert not (root / "metadata.json").exists()


def test_archive_recovery_uses_the_journal_entry_month(tmp_path: Path):
    paths = _paths(tmp_path)
    _item(paths, "TP-1")
    root = paths.workspace_dir / "archived"
    root.mkdir(parents=True)
    (root / ".transaction.json").write_text(
        json.dumps(
            {
                "operation": "archive",
                "item_id": "TP-1",
                "archive_month": "2026-07",
                "metadata": {
                    "original_id": "TP-1",
                    "project_key": "TP",
                    "archived_at": "2026-07-01T00:00:00Z",
                    "original_status": "done",
                },
            }
        ),
        encoding="utf-8",
    )

    assert archive_service.archive_items(paths, []) == []
    assert (root / "2026-07" / "TP-1.yaml").is_file()
    assert json.loads((root / "2026-07" / "metadata.json").read_text())["TP-1"]
    assert not (root / ".transaction.json").exists()
