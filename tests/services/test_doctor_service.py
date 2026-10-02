"""Tests for the workspace doctor service (spec 0010 R3, TP-139)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from taskpilot.core.item_io import write_item
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item, ItemLinks, ItemStatus, ItemType, Priority
from taskpilot.core.validation import validate_workspace
from taskpilot.services import doctor_service, item_service, project_service

NOW = "2026-01-01T00:00:00Z"
LATER = "2026-02-01T00:00:00Z"


@pytest.fixture
def paths(tmp_path: Path) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(paths, key="TP", name="Test", now=NOW)
    return paths


def _write(
    paths: WorkspacePaths,
    item_id: str,
    *,
    status: ItemStatus = ItemStatus.backlog,
    parent_id: str | None = None,
    blocks: list[str] | None = None,
    relates_to: list[str] | None = None,
) -> Path:
    links = None
    if blocks or relates_to:
        links = ItemLinks(blocks=blocks or [], relates_to=relates_to or [])
    return write_item(
        paths,
        Item(
            schema_version=1,
            id=item_id,
            title=item_id,
            type=ItemType.task,
            status=status,
            priority=Priority.normal,
            created_at=NOW,
            updated_at=NOW,
            parent_id=parent_id,
            links=links,
        ),
    )


def _snapshot(paths: WorkspacePaths) -> dict[str, bytes]:
    return {
        str(p.relative_to(paths.root)): p.read_bytes()
        for p in sorted(paths.workspace_dir.rglob("*"))
        if p.is_file()
    }


def _seed_dangling(paths: WorkspacePaths) -> None:
    _write(paths, "TP-1", status=ItemStatus.deleted)
    _write(paths, "TP-2", blocks=["TP-99"], relates_to=["TP-1"])
    _write(paths, "TP-3", parent_id="TP-77")


def test_clean_workspace_has_empty_plan(paths):
    _write(paths, "TP-1")
    plan = doctor_service.plan_fixes(paths)
    assert plan.fixes == []
    assert plan.manual == []


def test_plan_lists_safe_fixes_in_deterministic_order_without_writing(paths):
    _seed_dangling(paths)
    before = _snapshot(paths)

    plan = doctor_service.plan_fixes(paths)

    assert [(f.kind, f.item_id, f.field, f.target) for f in plan.fixes] == [
        ("remove_link", "TP-2", "links.blocks", "TP-99"),
        ("remove_link", "TP-2", "links.relates_to", "TP-1"),
        ("clear_parent", "TP-3", "parent_id", "TP-77"),
    ]
    assert [f.path for f in plan.fixes] == [
        ".taskpilot/items/TP-2.yaml",
        ".taskpilot/items/TP-2.yaml",
        ".taskpilot/items/TP-3.yaml",
    ]
    assert all(f.description for f in plan.fixes)
    assert plan.manual == []
    assert _snapshot(paths) == before
    assert doctor_service.plan_fixes(paths) == plan


def test_apply_repairs_files_and_is_idempotent(paths):
    _seed_dangling(paths)

    result = doctor_service.apply_fixes(paths, now=LATER)

    assert len(result.applied) == 3
    tp2 = item_service.read_item(paths, "TP-2")
    tp3 = item_service.read_item(paths, "TP-3")
    assert (tp2.links is None) or (
        tp2.links.blocks == [] and tp2.links.relates_to == []
    )
    assert tp3.parent_id is None
    assert tp2.updated_at == LATER and tp3.updated_at == LATER
    codes = {(f.item_id, f.code) for f in result.report.findings}
    assert not any(
        code in {"missing_reference", "link_to_deleted"} for _, code in codes
    )

    again = doctor_service.apply_fixes(paths, now=LATER)
    assert again.applied == []


def test_parent_pointing_at_deleted_item_is_manual(paths):
    _write(paths, "TP-1", status=ItemStatus.deleted)
    _write(paths, "TP-2", parent_id="TP-1")
    plan = doctor_service.plan_fixes(paths)
    assert plan.fixes == []
    assert [(f.item_id, f.code, f.field) for f in plan.manual] == [
        ("TP-2", "link_to_deleted", "parent_id")
    ]


def test_invalid_yaml_is_manual_and_untouched_by_apply(paths):
    bad = paths.items_dir / "TP-5.yaml"
    bad.write_text("id: [unclosed\n", encoding="utf-8")
    _write(paths, "TP-2", blocks=["TP-99"])

    plan = doctor_service.plan_fixes(paths)
    assert [f.code for f in plan.manual] == ["invalid_yaml"]

    doctor_service.apply_fixes(paths, now=LATER)
    assert bad.read_text(encoding="utf-8") == "id: [unclosed\n"


def test_archived_source_with_dangling_link_is_manual(paths):
    _write(paths, "TP-4", blocks=["TP-99"])
    month = paths.workspace_dir / "archived" / "2026-01"
    month.mkdir(parents=True)
    os.replace(paths.item_file("TP-4"), month / "TP-4.yaml")
    (month / "metadata.json").write_text(
        json.dumps(
            {
                "TP-4": {
                    "original_id": "TP-4",
                    "project_key": "TP",
                    "archived_at": "2026-01-15T00:00:00Z",
                    "original_status": "backlog",
                }
            }
        ),
        encoding="utf-8",
    )
    original = (month / "TP-4.yaml").read_bytes()

    plan = doctor_service.plan_fixes(paths)
    assert plan.fixes == []
    assert [(f.item_id, f.code) for f in plan.manual] == [("TP-4", "missing_reference")]

    doctor_service.apply_fixes(paths, now=LATER)
    assert (month / "TP-4.yaml").read_bytes() == original


def test_legacy_archive_storage_is_planned_and_migrated(paths):
    _write(paths, "TP-1", status=ItemStatus.done)
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

    plan = doctor_service.plan_fixes(paths)
    assert [(f.kind, f.path, f.item_id) for f in plan.fixes] == [
        ("migrate_archive_storage", ".taskpilot/archived/metadata.json", None)
    ]

    result = doctor_service.apply_fixes(paths)
    assert [f.kind for f in result.applied] == ["migrate_archive_storage"]
    assert (root / "2026-06" / "TP-1.yaml").is_file()
    assert not (root / "metadata.json").exists()
    assert doctor_service.plan_fixes(paths).fixes == []


def test_plan_to_dict_is_json_serializable_and_stable(paths):
    _seed_dangling(paths)
    first = json.dumps(doctor_service.plan_fixes(paths).to_dict(), sort_keys=False)
    second = json.dumps(doctor_service.plan_fixes(paths).to_dict(), sort_keys=False)
    assert first == second
    payload = json.loads(first)
    assert set(payload) == {"fixes", "manual"}
    assert set(payload["fixes"][0]) == {
        "kind",
        "item_id",
        "path",
        "field",
        "target",
        "description",
    }


def test_validation_report_matches_after_apply(paths):
    _seed_dangling(paths)
    result = doctor_service.apply_fixes(paths, now=LATER)
    assert result.report == validate_workspace(paths)


def test_item_with_several_dangling_references_is_fully_repaired(paths):
    _write(paths, "TP-1", status=ItemStatus.deleted)
    _write(
        paths,
        "TP-2",
        parent_id="TP-77",
        blocks=["TP-99", "TP-50"],
        relates_to=["TP-1"],
    )

    plan = doctor_service.plan_fixes(paths)
    assert [(f.kind, f.field, f.target) for f in plan.fixes] == [
        ("remove_link", "links.blocks", "TP-50"),
        ("remove_link", "links.blocks", "TP-99"),
        ("remove_link", "links.relates_to", "TP-1"),
        ("clear_parent", "parent_id", "TP-77"),
    ]

    result = doctor_service.apply_fixes(paths, now=LATER)
    assert len(result.applied) == 4
    item = item_service.read_item(paths, "TP-2")
    assert item.parent_id is None
    assert item.links is None or (
        item.links.blocks == [] and item.links.relates_to == []
    )
    assert doctor_service.apply_fixes(paths, now=LATER).applied == []


def _seed_conflicting_legacy_archive(paths: WorkspacePaths) -> list[Path]:
    _write(paths, "TP-1", status=ItemStatus.done)
    root = paths.workspace_dir / "archived"
    month = root / "2026-06"
    month.mkdir(parents=True)
    os.replace(paths.item_file("TP-1"), root / "TP-1.yaml")
    (month / "TP-1.yaml").write_text("different bytes\n", encoding="utf-8")
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
    return [root / "TP-1.yaml", month / "TP-1.yaml"]


def test_conflicting_legacy_archive_is_reported_failed_and_items_still_fixed(paths):
    files = _seed_conflicting_legacy_archive(paths)
    before = [f.read_bytes() for f in files]
    _write(paths, "TP-2", blocks=["TP-99"])

    result = doctor_service.apply_fixes(paths, now=LATER)

    assert [f.fix.kind for f in result.failed] == ["migrate_archive_storage"]
    assert "conflict" in result.failed[0].error.lower()
    assert [f.kind for f in result.applied] == ["remove_link"]
    assert [f.read_bytes() for f in files] == before


def _write_raw(paths: WorkspacePaths, name: str, text: str) -> Path:
    target = paths.items_dir / name
    target.write_text(text, encoding="utf-8")
    return target


def test_schema_invalid_target_is_known_and_never_unlinked(paths):
    # C1: TP-1 fails schema validation but still exists; references stay valid.
    _write_raw(
        paths,
        "TP-1.yaml",
        "schema_version: 1\nid: TP-1\ntitle: TP-1\ntype: task\nstatus: bogus\n"
        f"priority: normal\ncreated_at: '{NOW}'\nupdated_at: '{NOW}'\n",
    )
    _write(paths, "TP-2", blocks=["TP-1"])
    _write(paths, "TP-3", parent_id="TP-1")
    before = _snapshot(paths)

    plan = doctor_service.plan_fixes(paths)
    result = doctor_service.apply_fixes(paths, now=LATER)

    assert plan.fixes == []
    assert result.applied == [] and result.failed == []
    assert _snapshot(paths) == before


def test_invalid_yaml_target_is_known_by_filename(paths):
    # L3: a merge-conflicted file must not cause references to it to be stripped.
    _write_raw(paths, "TP-1.yaml", "<<<<<<< HEAD\nid: TP-1\n=======\n")
    _write(paths, "TP-2", relates_to=["TP-1"])

    assert doctor_service.plan_fixes(paths).fixes == []


def test_fix_set_is_a_subset_of_validator_findings(paths):
    _seed_dangling(paths)
    plan = doctor_service.plan_fixes(paths)
    report = validate_workspace(paths)
    reference = [
        f for f in report.findings if f.code in {"missing_reference", "link_to_deleted"}
    ]
    covered = [f for f in reference if f not in plan.manual]
    assert len(covered) == len(plan.fixes)


def test_item_whose_repair_would_still_be_rejected_is_left_manual(paths):
    # H1: a hierarchy violation on TP-2 makes any rewrite fail; TP-3 is still fixed.
    _write(paths, "TP-1")
    _write(paths, "TP-2", parent_id="TP-1", blocks=["TP-99"])
    _write(paths, "TP-3", blocks=["TP-98"])

    plan = doctor_service.plan_fixes(paths)
    assert [(f.item_id, f.target) for f in plan.fixes] == [("TP-3", "TP-98")]
    assert ("TP-2", "missing_reference") in {(f.item_id, f.code) for f in plan.manual}

    result = doctor_service.apply_fixes(paths, now=LATER)
    assert [f.item_id for f in result.applied] == ["TP-3"]
    assert result.failed == []
    assert doctor_service.apply_fixes(paths, now=LATER).applied == []


def test_id_filename_mismatch_and_duplicate_files_are_not_repaired(paths):
    _write(paths, "TP-5", blocks=["TP-99"])
    mismatch = paths.items_dir / "TP-6.yaml"
    mismatch.write_bytes(paths.item_file("TP-5").read_bytes())
    original = mismatch.read_bytes()

    plan = doctor_service.plan_fixes(paths)
    assert all(f.path != ".taskpilot/items/TP-6.yaml" for f in plan.fixes)
    doctor_service.apply_fixes(paths, now=LATER)
    assert mismatch.read_bytes() == original


def test_malformed_legacy_metadata_fails_alone(paths):
    root = paths.workspace_dir / "archived"
    root.mkdir(parents=True)
    (root / "metadata.json").write_text(
        json.dumps({"TP-1": {"original_id": "WRONG"}}), encoding="utf-8"
    )
    _write(paths, "TP-2", blocks=["TP-99"])

    result = doctor_service.apply_fixes(paths, now=LATER)

    assert [f.fix.kind for f in result.failed] == ["migrate_archive_storage"]
    assert [f.item_id for f in result.applied] == ["TP-2"]
