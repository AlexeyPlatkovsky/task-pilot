"""Workspace doctor: preview and apply safe, deterministic repairs (spec ``0010`` R3).

Only repairs whose outcome is unambiguous are offered:

- ``remove_link`` — an active item's ``links.blocks``/``links.relates_to`` entry
  that points at a missing or soft-deleted item;
- ``clear_parent`` — an active item's ``parent_id`` that points at a missing item;
- ``migrate_archive_storage`` — root-level (legacy) archive metadata still exists.

Safety rules:

- every reference fix corresponds to exactly one validator finding with the same
  path, field, and message, so the doctor never repairs what validation accepts;
- an id counts as known when any item file carries it, by filename stem or by a
  recoverable ``id`` value, so a typo or merge conflict in one file never strips
  references to it from others;
- files with ``id_filename_mismatch`` or ``duplicate_id`` findings are not
  repaired, and each item's repair is dry-run through the item service so the plan
  only offers fixes that will be accepted.

Everything else the validator reports stays in ``manual``. Archived item files are
never rewritten. :func:`apply_fixes` recomputes the plan from disk, writes each item
through the item service, and reports per-fix failures instead of aborting.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ValidationError

from taskpilot.core.item_io import ItemParseError, parse_item_file
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item
from taskpilot.core.validation import Finding, ValidationReport, validate_workspace
from taskpilot.core.yaml_io import load_yaml
from taskpilot.services import archive_service, item_service
from taskpilot.services.errors import ServiceError

__all__ = [
    "FixKind",
    "DoctorFix",
    "DoctorFailure",
    "DoctorPlan",
    "DoctorResult",
    "plan_fixes",
    "apply_fixes",
]

FixKind = Literal["remove_link", "clear_parent", "migrate_archive_storage"]

_LINK_FIELDS = ("blocks", "relates_to")
_UNREPAIRABLE_FILE_CODES = {"id_filename_mismatch", "duplicate_id"}


class DoctorFix(BaseModel):
    kind: FixKind
    item_id: str | None
    path: str
    field: str | None
    target: str | None
    description: str

    def sort_key(self) -> tuple[str, str, str, str]:
        return (self.path, self.field or "", self.target or "", self.kind)

    def to_dict(self) -> dict:
        return self.model_dump()


class DoctorFailure(BaseModel):
    fix: DoctorFix
    error: str

    def to_dict(self) -> dict:
        return {"fix": self.fix.to_dict(), "error": self.error}


class DoctorPlan(BaseModel):
    fixes: list[DoctorFix]
    manual: list[Finding]

    def to_dict(self) -> dict:
        return {
            "fixes": [f.to_dict() for f in self.fixes],
            "manual": [f.to_dict() for f in self.manual],
        }


class DoctorResult(BaseModel):
    applied: list[DoctorFix]
    failed: list[DoctorFailure]
    report: ValidationReport

    def to_dict(self) -> dict:
        return {
            "applied": [f.to_dict() for f in self.applied],
            "failed": [f.to_dict() for f in self.failed],
            "report": self.report.to_dict(),
        }


def _item_files(paths: WorkspacePaths) -> list[Path]:
    files = (
        [p for p in paths.items_dir.glob("*.yaml") if p.is_file()]
        if paths.items_dir.is_dir()
        else []
    )
    archived_dir = paths.workspace_dir / "archived"
    if archived_dir.is_dir():
        files.extend(p for p in archived_dir.rglob("*.yaml") if p.is_file())
    return files


def _known_ids(paths: WorkspacePaths) -> set[str]:
    """Every id any item file claims: filename stems plus recoverable ``id`` values."""
    known: set[str] = set()
    for file in _item_files(paths):
        known.add(file.stem)
        try:
            data = load_yaml(file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            continue
        if isinstance(data, dict) and isinstance(data.get("id"), str):
            known.add(data["id"])
    return known


def _deleted_ids(paths: WorkspacePaths) -> set[str]:
    return {
        item.id
        for item in item_service.list_items(
            paths, include_deleted=True, include_archived=True
        )
        if item.status == "deleted"
    }


def _reference_message(field: str, target: str, *, deleted: bool) -> str:
    # Mirrors core.validation's reference findings; a fix is offered only when the
    # validator produced this exact finding for the same path and field.
    state = "deleted" if deleted else "unknown"
    return f"{field} references {state} item: {target}"


def _candidate_fixes(
    rel: str,
    item: Item,
    *,
    known: set[str],
    deleted: set[str],
    reported: set[tuple[str, str | None, str]],
) -> list[DoctorFix]:
    fixes: list[DoctorFix] = []
    if item.links is not None:
        for link_type in _LINK_FIELDS:
            field = f"links.{link_type}"
            for target in getattr(item.links, link_type):
                if target in known and target not in deleted:
                    continue
                message = _reference_message(field, target, deleted=target in known)
                if (rel, field, message) not in reported:
                    continue
                fixes.append(
                    DoctorFix(
                        kind="remove_link",
                        item_id=item.id,
                        path=rel,
                        field=field,
                        target=target,
                        description=f"Remove {field} -> {target} from {item.id}",
                    )
                )
    parent = item.parent_id
    if parent is not None and parent not in known:
        message = _reference_message("parent_id", parent, deleted=False)
        if (rel, "parent_id", message) in reported:
            fixes.append(
                DoctorFix(
                    kind="clear_parent",
                    item_id=item.id,
                    path=rel,
                    field="parent_id",
                    target=parent,
                    description=f"Clear parent_id -> {parent} from {item.id}",
                )
            )
    return fixes


def _update_fields(item: Item, fixes: list[DoctorFix]) -> dict[str, object]:
    fields: dict[str, object] = {}
    removals = {(f.field, f.target) for f in fixes if f.kind == "remove_link"}
    if removals and item.links is not None:
        fields["links"] = {
            link_type: [
                t
                for t in getattr(item.links, link_type)
                if (f"links.{link_type}", t) not in removals
            ]
            for link_type in _LINK_FIELDS
        }
    if any(f.kind == "clear_parent" for f in fixes):
        fields["parent_id"] = None
    return fields


def _covers(fix: DoctorFix, finding: Finding) -> bool:
    if fix.kind == "migrate_archive_storage" or fix.path != finding.path:
        return False
    if fix.field != finding.field or fix.target is None or fix.field is None:
        return False
    return finding.message in {
        _reference_message(fix.field, fix.target, deleted=False),
        _reference_message(fix.field, fix.target, deleted=True),
    }


def plan_fixes(paths: WorkspacePaths) -> DoctorPlan:
    """Compute the repair plan without writing anything."""
    report = validate_workspace(paths)
    reported = {(f.path, f.field, f.message) for f in report.findings}
    blocked = {f.path for f in report.findings if f.code in _UNREPAIRABLE_FILE_CODES}
    known = _known_ids(paths)
    deleted = _deleted_ids(paths)

    fixes: list[DoctorFix] = []
    if paths.items_dir.is_dir():
        for file in sorted(paths.items_dir.glob("*.yaml")):
            rel = paths.relative_posix(file)
            if not file.is_file() or rel in blocked:
                continue
            try:
                item = parse_item_file(file)
            except (ItemParseError, ValidationError, UnicodeDecodeError, OSError):
                continue
            if item.id != file.stem:
                continue
            item_fixes = _candidate_fixes(
                rel, item, known=known, deleted=deleted, reported=reported
            )
            if not item_fixes:
                continue
            try:
                item_service.prepare_update(
                    paths, item.id, **_update_fields(item, item_fixes)
                )
            except ServiceError:
                # The repaired item would still be rejected (e.g. a hierarchy
                # violation); leave its findings for manual attention.
                continue
            fixes.extend(item_fixes)

    if archive_service.legacy_archive_ids(paths):
        metadata = paths.workspace_dir / "archived" / "metadata.json"
        fixes.append(
            DoctorFix(
                kind="migrate_archive_storage",
                item_id=None,
                path=paths.relative_posix(metadata),
                field=None,
                target=None,
                description="Move legacy archive data into monthly archive storage",
            )
        )

    fixes.sort(key=DoctorFix.sort_key)
    manual = [f for f in report.findings if not any(_covers(x, f) for x in fixes)]
    return DoctorPlan(fixes=fixes, manual=manual)


def apply_fixes(paths: WorkspacePaths, *, now: str | None = None) -> DoctorResult:
    """Apply every safe fix from a freshly computed plan and re-validate.

    Each item is written once with all of its fixes. A fix the services reject is
    reported in ``failed`` with the error, and the remaining fixes still run.
    """
    plan = plan_fixes(paths)
    applied: list[DoctorFix] = []
    failed: list[DoctorFailure] = []

    by_item: dict[str, list[DoctorFix]] = defaultdict(list)
    for fix in plan.fixes:
        if fix.kind != "migrate_archive_storage":
            by_item[fix.item_id or ""].append(fix)

    for item_id, item_fixes in sorted(
        by_item.items(), key=lambda kv: kv[1][0].sort_key()
    ):
        try:
            current = item_service.read_item(paths, item_id)
            item_service.update_item(
                paths, item_id, now=now, **_update_fields(current, item_fixes)
            )
        except ServiceError as exc:
            failed.extend(DoctorFailure(fix=f, error=str(exc)) for f in item_fixes)
            continue
        applied.extend(item_fixes)

    for fix in plan.fixes:
        if fix.kind != "migrate_archive_storage":
            continue
        try:
            archive_service.migrate_legacy_archives(paths)
        except ServiceError as exc:
            failed.append(DoctorFailure(fix=fix, error=str(exc)))
            continue
        applied.append(fix)

    applied.sort(key=DoctorFix.sort_key)
    failed.sort(key=lambda f: f.fix.sort_key())
    return DoctorResult(
        applied=applied, failed=failed, report=validate_workspace(paths)
    )
