"""Tests for archive_service: threshold, scan, archive, migrate, unarchive, list, is_archived."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item, ItemStatus, ItemType, Priority
from taskpilot.services import archive_service
from taskpilot.services.errors import ConflictError, NotFound, ValidationFailed


# ── Fixtures ──────────────────────────────────────────────────────────────


def _paths(tmp_path: Path) -> WorkspacePaths:
    return WorkspacePaths.for_root(tmp_path)


def _create_project(
    paths: WorkspacePaths, key: str = "TP", now: str = "2026-08-01T00:00:00Z"
) -> None:
    """Create a minimal project.yaml in the workspace."""
    from taskpilot.services import project_service

    project_service.create_project(paths, key=key, name="TestProject", now=now)


def _create_item(
    paths: WorkspacePaths,
    item_id: str,
    status: ItemStatus,
    updated_at: str,
    created_at: str | None = None,
) -> Item:
    """Create a minimal item YAML file."""
    from taskpilot.core.item_io import write_item
    from taskpilot.core.models import Item

    if created_at is None:
        created_at = updated_at
    item = Item(
        schema_version=1,
        id=item_id,
        title=f"Item {item_id}",
        type=ItemType.task,
        status=status,
        priority=Priority.normal,
        created_at=created_at,
        updated_at=updated_at,
    )
    return write_item(paths, item)


def _make_future_item(
    paths: WorkspacePaths,
    item_id: str,
    status: ItemStatus,
    days_ago: int,
) -> Item:
    """Create an item that is `days_ago` days old."""
    now = datetime(2026, 8, 15, tzinfo=timezone.utc)
    updated = now - timedelta(days=days_ago)
    created = updated - timedelta(days=1)
    return _create_item(
        paths,
        item_id,
        status,
        updated.isoformat().replace("+00:00", "Z"),
        created.isoformat().replace("+00:00", "Z"),
    )


def _monthly_archive_file(paths: WorkspacePaths, item_id: str) -> Path:
    return archive_service._metadata_file(paths, "2026-08").parent / f"{item_id}.yaml"


def _monthly_metadata_file(paths: WorkspacePaths) -> Path:
    return archive_service._metadata_file(paths, "2026-08")


# ── get_archive_threshold ─────────────────────────────────────────────────


class TestGetArchiveThreshold:
    def test_returns_default_14_when_not_set(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        assert archive_service.get_archive_threshold(paths) == 14

    def test_returns_custom_value(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        archive_service.set_archive_threshold(paths, 30)
        assert archive_service.get_archive_threshold(paths) == 30

    def test_returns_1_for_minimum(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        archive_service.set_archive_threshold(paths, 1)
        assert archive_service.get_archive_threshold(paths) == 1

    def test_returns_3650_for_maximum(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        archive_service.set_archive_threshold(paths, 3650)
        assert archive_service.get_archive_threshold(paths) == 3650


# ── set_archive_threshold ────────────────────────────────────────────────


class TestSetArchiveThreshold:
    def test_rejects_zero(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        with pytest.raises(ValidationFailed, match="between 1 and 3650"):
            archive_service.set_archive_threshold(paths, 0)

    def test_rejects_negative(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        with pytest.raises(ValidationFailed, match="between 1 and 3650"):
            archive_service.set_archive_threshold(paths, -1)

    def test_rejects_above_max(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        with pytest.raises(ValidationFailed, match="between 1 and 3650"):
            archive_service.set_archive_threshold(paths, 3651)

    def test_accepts_boundary_values(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        assert archive_service.set_archive_threshold(paths, 1) == 1
        assert archive_service.set_archive_threshold(paths, 3650) == 3650

    def test_persists_to_project_yaml(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        archive_service.set_archive_threshold(paths, 7)
        project = archive_service.get_archive_threshold(paths)
        assert project == 7


# ── scan_eligible_items ───────────────────────────────────────────────────


class TestScanEligibleItems:
    def test_returns_empty_when_no_items(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert result == []

    def test_excludes_backlog_items(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.backlog, 30)
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert result == []

    def test_excludes_ready_items(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.ready, 30)
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert result == []

    def test_excludes_in_progress_items(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.in_progress, 30)
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert result == []

    def test_includes_done_items_past_threshold(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert len(result) == 1
        assert result[0].id == "TP-1"

    def test_includes_cancelled_items_past_threshold(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.cancelled, 15)
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert len(result) == 1
        assert result[0].id == "TP-1"

    def test_includes_deleted_items_past_threshold(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.deleted, 15)
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert len(result) == 1
        assert result[0].id == "TP-1"

    def test_excludes_items_within_threshold(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 10)
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert result == []

    def test_excludes_already_archived_items(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 30)
        # Pre-populate metadata.json with TP-1
        meta_path = archive_service._metadata_file(paths)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(
            json.dumps({"TP-1": {"original_id": "TP-1"}}), encoding="utf-8"
        )
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert result == []

    def test_excludes_invalid_items(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        # Write an invalid YAML file
        item_file = paths.item_file("TP-1")
        item_file.write_text("not: valid: yaml: [", encoding="utf-8")
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert result == []

    def test_boundary_exactly_at_threshold(self, tmp_path: Path):
        """Item exactly at threshold (14 days) should be eligible."""
        paths = _paths(tmp_path)
        _create_project(paths)
        now = datetime(2026, 8, 15, tzinfo=timezone.utc)
        updated = now - timedelta(days=14)
        created = updated - timedelta(days=1)
        _create_item(
            paths,
            "TP-1",
            ItemStatus.done,
            updated.isoformat().replace("+00:00", "Z"),
            created.isoformat().replace("+00:00", "Z"),
        )
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert len(result) == 1

    def test_boundary_one_day_before_threshold(self, tmp_path: Path):
        """Item 13 days old should NOT be eligible with 14-day default."""
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 13)
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert result == []

    def test_respects_custom_threshold(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        archive_service.set_archive_threshold(paths, 7)
        _make_future_item(paths, "TP-1", ItemStatus.done, 10)
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert len(result) == 1

    def test_excludes_future_updated_at(self, tmp_path: Path):
        """Items with updated_at in the future should not be eligible."""
        paths = _paths(tmp_path)
        _create_project(paths)
        now = datetime(2026, 8, 15, tzinfo=timezone.utc)
        future = now + timedelta(days=5)
        _create_item(
            paths, "TP-1", ItemStatus.done, future.isoformat().replace("+00:00", "Z")
        )
        result = archive_service.scan_eligible_items(paths, now="2026-08-15T00:00:00Z")
        assert result == []


# ── archive_items ─────────────────────────────────────────────────────────


class TestArchiveItems:
    def test_archives_eligible_items(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        archived = archive_service.archive_items(
            paths, ["TP-1"], now="2026-08-15T00:00:00Z"
        )
        assert archived == ["TP-1"]
        # File should exist in archived/
        assert _monthly_archive_file(paths, "TP-1").exists()
        # File should NOT exist in items/
        assert not paths.item_file("TP-1").exists()

    def test_is_idempotent(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        _make_future_item(paths, "TP-2", ItemStatus.done, 15)
        archive_service.archive_items(
            paths, ["TP-1", "TP-2"], now="2026-08-15T00:00:00Z"
        )
        # Second call should return empty (already archived)
        archived = archive_service.archive_items(
            paths, ["TP-1"], now="2026-08-15T00:00:00Z"
        )
        assert archived == []

    def test_skips_non_eligible_items(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.backlog, 30)
        archived = archive_service.archive_items(
            paths, ["TP-1"], now="2026-08-15T00:00:00Z"
        )
        assert archived == []

    def test_skips_invalid_items(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        item_file = paths.item_file("TP-1")
        item_file.write_text("invalid yaml content [[[", encoding="utf-8")
        archived = archive_service.archive_items(
            paths, ["TP-1"], now="2026-08-15T00:00:00Z"
        )
        assert archived == []

    def test_creates_metadata_json(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        archive_service.archive_items(paths, ["TP-1"], now="2026-08-15T00:00:00Z")
        meta_path = _monthly_metadata_file(paths)
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert "TP-1" in meta
        assert meta["TP-1"]["project_key"] == "TP"
        assert meta["TP-1"]["original_status"] == "done"

    def test_preserves_source_updated_at(self, tmp_path: Path):
        """Moving file should not modify source's updated_at (file is deleted, not rewritten)."""
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        # Read the original updated_at from the item file before archiving
        original_file = paths.item_file("TP-1")
        original_content = original_file.read_text(encoding="utf-8")
        # After archive, the file in archived/ should have the same content
        archive_service.archive_items(paths, ["TP-1"], now="2026-08-15T00:00:00Z")
        archived_file = _monthly_archive_file(paths, "TP-1")
        archived_content = archived_file.read_text(encoding="utf-8")
        # The content should be identical (file moved, not rewritten)
        assert original_content == archived_content

    def test_archives_multiple_items(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        _make_future_item(paths, "TP-2", ItemStatus.cancelled, 20)
        _make_future_item(paths, "TP-3", ItemStatus.deleted, 25)
        archived = archive_service.archive_items(
            paths, ["TP-1", "TP-2", "TP-3"], now="2026-08-15T00:00:00Z"
        )
        assert sorted(archived) == ["TP-1", "TP-2", "TP-3"]

    def test_creates_archived_directory(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        # Ensure archived/ doesn't exist yet
        assert not archive_service._archived_dir(paths).exists()
        archive_service.archive_items(paths, ["TP-1"], now="2026-08-15T00:00:00Z")
        assert archive_service._archived_dir(paths).exists()

    def test_empty_list_does_nothing(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        archived = archive_service.archive_items(paths, [], now="2026-08-15T00:00:00Z")
        assert archived == []


class TestArchiveTransactions:
    def test_rejects_invalid_journal_without_relocating_item(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        original = paths.item_file("TP-1").read_bytes()
        archive_service._ensure_archived_dir(paths)
        archive_service._transaction_file(paths).write_text(
            json.dumps({"operation": "archive", "item_id": "TP-1"}),
            encoding="utf-8",
        )

        with pytest.raises(ValidationFailed, match="invalid content"):
            archive_service.archive_items(paths, [], now="2026-08-16T00:00:00Z")

        assert paths.item_file("TP-1").read_bytes() == original
        assert not (archive_service._archived_dir(paths) / "TP-1.yaml").exists()
        assert archive_service._transaction_file(paths).exists()

    def test_recovers_archive_after_metadata_write_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        original = paths.item_file("TP-1").read_bytes()

        with monkeypatch.context() as failing:
            failing.setattr(
                archive_service,
                "_save_metadata",
                lambda _paths, _metadata: (_ for _ in ()).throw(OSError("disk full")),
            )
            with pytest.raises(OSError, match="disk full"):
                archive_service.archive_items(
                    paths, ["TP-1"], now="2026-08-15T00:00:00Z"
                )

        assert archive_service._transaction_file(paths).exists()
        assert not paths.item_file("TP-1").exists()
        assert _monthly_archive_file(paths, "TP-1").exists()

        assert (
            archive_service.archive_items(paths, [], now="2026-08-16T00:00:00Z") == []
        )
        metadata = json.loads(_monthly_metadata_file(paths).read_text())
        assert metadata["TP-1"]["archived_at"] == "2026-08-15T00:00:00Z"
        assert (_monthly_archive_file(paths, "TP-1")).read_bytes() == original
        assert not archive_service._transaction_file(paths).exists()

    def test_records_archive_journal_before_relocation_and_recovers(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        original = paths.item_file("TP-1").read_bytes()
        real_replace = archive_service.os.replace

        def fail_item_relocation(src, dst):
            if Path(src) == paths.item_file("TP-1"):
                raise OSError("relocation failed")
            return real_replace(src, dst)

        with monkeypatch.context() as failing:
            failing.setattr(archive_service.os, "replace", fail_item_relocation)
            with pytest.raises(OSError, match="relocation failed"):
                archive_service.archive_items(
                    paths, ["TP-1"], now="2026-08-15T00:00:00Z"
                )

        journal = json.loads(archive_service._transaction_file(paths).read_text())
        assert journal["operation"] == "archive"
        assert journal["item_id"] == "TP-1"
        assert journal["metadata"]["archived_at"] == "2026-08-15T00:00:00Z"
        assert paths.item_file("TP-1").read_bytes() == original

        assert (
            archive_service.archive_items(paths, [], now="2026-08-16T00:00:00Z") == []
        )
        assert (_monthly_archive_file(paths, "TP-1")).read_bytes() == original
        metadata = json.loads(_monthly_metadata_file(paths).read_text())
        assert metadata["TP-1"]["archived_at"] == "2026-08-15T00:00:00Z"
        assert not archive_service._transaction_file(paths).exists()

    def test_recovers_unarchive_after_metadata_write_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        _make_future_item(paths, "TP-2", ItemStatus.done, 15)
        archive_service.archive_items(
            paths, ["TP-1", "TP-2"], now="2026-08-15T00:00:00Z"
        )
        original = _monthly_archive_file(paths, "TP-1").read_bytes()

        with monkeypatch.context() as failing:
            failing.setattr(
                archive_service,
                "_save_metadata",
                lambda _paths, _metadata: (_ for _ in ()).throw(OSError("disk full")),
            )
            with pytest.raises(OSError, match="disk full"):
                archive_service.unarchive_item(paths, "TP-1")

        assert archive_service._transaction_file(paths).exists()
        assert paths.item_file("TP-1").exists()
        assert not _monthly_archive_file(paths, "TP-1").exists()

        assert (
            archive_service.archive_items(paths, [], now="2026-08-16T00:00:00Z") == []
        )
        metadata = json.loads(_monthly_metadata_file(paths).read_text())
        assert sorted(metadata) == ["TP-2"]
        assert paths.item_file("TP-1").read_bytes() == original
        assert not archive_service._transaction_file(paths).exists()

    def test_archive_operation_waits_for_workspace_lock(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        attempting_lock = threading.Event()
        acquired_lock = threading.Event()
        original_lock = archive_service._archive_lock

        @contextmanager
        def observed_lock(locked_paths: WorkspacePaths):
            attempting_lock.set()
            with original_lock(locked_paths):
                acquired_lock.set()
                yield

        def archive() -> list[str]:
            result = archive_service.archive_items(
                paths, ["TP-1"], now="2026-08-15T00:00:00Z"
            )
            return result

        monkeypatch.setattr(archive_service, "_archive_lock", observed_lock)
        with ThreadPoolExecutor(max_workers=1) as executor:
            with original_lock(paths):
                future = executor.submit(archive)
                assert attempting_lock.wait(timeout=1)
                assert not acquired_lock.wait(timeout=0.1)
            assert future.result() == ["TP-1"]
        metadata = json.loads(_monthly_metadata_file(paths).read_text())
        assert metadata["TP-1"]["archived_at"] == "2026-08-15T00:00:00Z"


# ── migrate_all_eligible ──────────────────────────────────────────────────


class TestMigrateAllEligible:
    def test_migrates_all_eligible(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        _make_future_item(paths, "TP-2", ItemStatus.cancelled, 20)
        _make_future_item(paths, "TP-3", ItemStatus.backlog, 30)  # not eligible
        archived = archive_service.migrate_all_eligible(
            paths, now="2026-08-15T00:00:00Z"
        )
        assert sorted(archived) == ["TP-1", "TP-2"]

    def test_returns_empty_when_none_eligible(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.backlog, 30)
        archived = archive_service.migrate_all_eligible(
            paths, now="2026-08-15T00:00:00Z"
        )
        assert archived == []


# ── unarchive_item ────────────────────────────────────────────────────────


class TestUnarchiveItem:
    def test_restores_item_to_items_dir(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        archive_service.archive_items(paths, ["TP-1"], now="2026-08-15T00:00:00Z")
        restored = archive_service.unarchive_item(paths, "TP-1")
        assert restored.id == "TP-1"
        assert paths.item_file("TP-1").exists()
        assert not _monthly_archive_file(paths, "TP-1").exists()

    def test_raises_not_found_when_not_archived(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        with pytest.raises(NotFound, match="not archived"):
            archive_service.unarchive_item(paths, "TP-999")

    def test_rejects_occupied_destination_without_changing_canonical_files(
        self, tmp_path: Path
    ):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        archive_service.archive_items(paths, ["TP-1"], now="2026-08-15T00:00:00Z")
        archived_file = _monthly_archive_file(paths, "TP-1")
        metadata_file = _monthly_metadata_file(paths)
        archived_before = archived_file.read_bytes()
        metadata_before = metadata_file.read_bytes()

        _create_item(
            paths,
            "TP-1",
            ItemStatus.backlog,
            updated_at="2026-08-15T00:00:00Z",
        )
        active_before = paths.item_file("TP-1").read_bytes()

        with pytest.raises(ConflictError, match="already exists"):
            archive_service.unarchive_item(paths, "TP-1")

        assert paths.item_file("TP-1").read_bytes() == active_before
        assert archived_file.read_bytes() == archived_before
        assert metadata_file.read_bytes() == metadata_before

    def test_removes_metadata_json_when_last_item(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        archive_service.archive_items(paths, ["TP-1"], now="2026-08-15T00:00:00Z")
        archive_service.unarchive_item(paths, "TP-1")
        assert not _monthly_metadata_file(paths).exists()

    def test_preserves_original_status(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.cancelled, 15)
        archive_service.archive_items(paths, ["TP-1"], now="2026-08-15T00:00:00Z")
        restored = archive_service.unarchive_item(paths, "TP-1")
        assert restored.status == ItemStatus.cancelled

    def test_preserves_created_at(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        # Read the original created_at from the item file before archiving
        original_file = paths.item_file("TP-1")
        original_content = original_file.read_text(encoding="utf-8")
        import re

        match = re.search(r"created_at: ['\"]?([^'\']+)['\"]?", original_content)
        assert match, "Could not find created_at in item file"
        original_created = match.group(1)
        archive_service.archive_items(paths, ["TP-1"], now="2026-08-15T00:00:00Z")
        restored = archive_service.unarchive_item(paths, "TP-1")
        assert restored.created_at == original_created


# ── list_archived_items ───────────────────────────────────────────────────


class TestListArchivedItems:
    def test_returns_empty_when_no_archived(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        result = archive_service.list_archived_items(paths)
        assert result == []

    def test_returns_archived_items(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        _make_future_item(paths, "TP-2", ItemStatus.cancelled, 20)
        archive_service.archive_items(
            paths, ["TP-1", "TP-2"], now="2026-08-15T00:00:00Z"
        )
        result = archive_service.list_archived_items(paths)
        assert len(result) == 2
        ids = {item.id for item in result}
        assert ids == {"TP-1", "TP-2"}

    def test_skips_invalid_archived_files(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        archive_service.archive_items(paths, ["TP-1"], now="2026-08-15T00:00:00Z")
        # Corrupt the archived file
        archived_file = _monthly_archive_file(paths, "TP-1")
        archived_file.write_text("invalid yaml [[[", encoding="utf-8")
        result = archive_service.list_archived_items(paths)
        assert result == []


# ── is_archived ───────────────────────────────────────────────────────────


class TestIsArchived:
    def test_returns_true_for_archived(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.done, 15)
        archive_service.archive_items(paths, ["TP-1"], now="2026-08-15T00:00:00Z")
        assert archive_service.is_archived(paths, "TP-1") is True

    def test_returns_false_for_active(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        _make_future_item(paths, "TP-1", ItemStatus.backlog, 30)
        assert archive_service.is_archived(paths, "TP-1") is False

    def test_returns_false_for_nonexistent(self, tmp_path: Path):
        paths = _paths(tmp_path)
        _create_project(paths)
        assert archive_service.is_archived(paths, "TP-999") is False
