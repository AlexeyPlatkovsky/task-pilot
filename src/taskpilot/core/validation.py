"""Item validation producing non-crashing findings (task F001-T7, F001-R6).

Validation never blocks loading: every problem becomes a :class:`Finding` with a
severity, stable code, file path, and message. Errors flip ``ok`` to ``False``
(and make ``taskpilot validate`` exit non-zero); warnings do not.

Covered rules (see ``docs/specs/0002`` "Validation"):

- unparseable YAML / non-mapping documents (error);
- required fields and valid enums/timestamps via the :class:`Item` model (error);
- ``id`` must match the filename stem (error);
- duplicate ``id`` across files (error on every offending file);
- ``parent_id`` and link targets must reference existing items (missing -> error;
  target is ``deleted`` -> warning);
- attachment paths must be relative and inside the repo (absolute/escape -> error;
  missing file -> warning).

Hierarchy *type* rules (epic/feature/task/bug parent-child) are F002-T3.
"""

from __future__ import annotations

from collections import defaultdict
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from taskpilot.core.comments import (
    CommentParseError,
    comment_filename_timestamp,
    parse_comment_text,
)
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item
from taskpilot.core.yaml_io import load_yaml

__all__ = ["Severity", "Finding", "ValidationReport", "validate_workspace"]


class Severity(str, Enum):
    error = "error"
    warning = "warning"


class Finding(BaseModel):
    """A single validation result. ``field``/``item_id`` are null when not applicable."""

    severity: Severity
    code: str
    path: str
    field: str | None = None
    item_id: str | None = None
    message: str

    def to_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "path": self.path,
            "field": self.field,
            "item_id": self.item_id,
            "message": self.message,
        }


class ValidationReport(BaseModel):
    """Aggregated findings. ``ok`` is True when there are no error-severity findings."""

    findings: list[Finding]

    @property
    def ok(self) -> bool:
        return not any(f.severity == Severity.error for f in self.findings)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.error)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.warning)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "summary": {"errors": self.error_count, "warnings": self.warning_count},
            "findings": [f.to_dict() for f in self.findings],
        }


def _finding_from_pydantic(err: dict, *, path: str, item_id: str | None) -> Finding:
    field = ".".join(str(p) for p in err["loc"])
    etype = err["type"]
    if etype == "missing":
        return Finding(
            severity=Severity.error, code="missing_required_field", path=path,
            field=field, item_id=item_id, message=f"Missing required field: {field}",
        )
    if etype == "enum":
        expected = err.get("ctx", {}).get("expected", "")
        return Finding(
            severity=Severity.error, code="invalid_enum", path=path, field=field,
            item_id=item_id, message=f"Invalid value for {field}: expected one of {expected}",
        )
    return Finding(
        severity=Severity.error, code="invalid_field", path=path, field=field,
        item_id=item_id, message=f"{field}: {err['msg']}",
    )


def _validate_attachment(value: str, *, paths: WorkspacePaths, path: str, item_id: str) -> Finding | None:
    if not value.strip():
        return Finding(
            severity=Severity.error, code="attachment_empty", path=path,
            field="attachments", item_id=item_id, message="Attachment path is empty",
        )
    if Path(value).is_absolute():
        return Finding(
            severity=Severity.error, code="attachment_not_relative", path=path,
            field="attachments", item_id=item_id,
            message=f"Attachment path must be relative: {value}",
        )
    resolved = (paths.root / value).resolve()
    if not resolved.is_relative_to(paths.root):
        return Finding(
            severity=Severity.error, code="attachment_outside_repo", path=path,
            field="attachments", item_id=item_id,
            message=f"Attachment path escapes the repository: {value}",
        )
    if not resolved.exists():
        return Finding(
            severity=Severity.warning, code="missing_attachment", path=path,
            field="attachments", item_id=item_id,
            message=f"Attachment file not found: {value}",
        )
    return None


def _validate_comments(paths: WorkspacePaths) -> list[Finding]:
    """Validate ``comments/<ITEM_ID>/*.md`` files without crashing the run.

    Reports unreadable/malformed comment files as errors and a filename whose
    timestamp does not match the frontmatter ``created_at`` as a warning. The
    owning item id is the comment folder name.
    """
    findings: list[Finding] = []
    if not paths.comments_dir.is_dir():
        return findings

    for item_dir in sorted(p for p in paths.comments_dir.iterdir() if p.is_dir()):
        item_id = item_dir.name
        for file in sorted(f for f in item_dir.glob("*.md") if f.is_file()):
            rel = paths.relative_posix(file)
            try:
                text = file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError) as exc:
                findings.append(Finding(severity=Severity.error, code="comment_unreadable", path=rel,
                                        item_id=item_id, message=f"Cannot read comment file as UTF-8: {exc}"))
                continue

            try:
                comment = parse_comment_text(text)
            except CommentParseError as exc:
                findings.append(Finding(severity=Severity.error, code="invalid_comment", path=rel,
                                        item_id=item_id, message=str(exc)))
                continue
            except ValidationError as exc:
                for err in exc.errors():
                    findings.append(_finding_from_pydantic(err, path=rel, item_id=item_id))
                continue

            expected = comment_filename_timestamp(file.name)
            if expected is None:
                findings.append(Finding(
                    severity=Severity.warning, code="comment_filename_not_timestamp", path=rel,
                    item_id=item_id, message=f"Comment filename does not encode a timestamp: {file.name}",
                ))
            elif expected != comment.created_at:
                findings.append(Finding(
                    severity=Severity.warning, code="comment_timestamp_mismatch", path=rel,
                    field="created_at", item_id=item_id,
                    message=f"created_at {comment.created_at!r} does not match filename timestamp {expected!r}",
                ))
    return findings


def validate_workspace(paths: WorkspacePaths) -> ValidationReport:
    """Validate every ``items/*.yaml`` and ``comments/**/*.md`` file in the workspace."""
    findings: list[Finding] = []
    valid_items: list[tuple[Item, str]] = []
    status_by_id: dict[str, str] = {}
    paths_by_id: dict[str, list[str]] = defaultdict(list)

    if paths.items_dir.is_dir():
        item_files = sorted(p for p in paths.items_dir.glob("*.yaml") if p.is_file())
    else:
        item_files = []

    for file in item_files:
        rel = paths.relative_posix(file)
        filename_id = file.stem
        try:
            text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            findings.append(Finding(severity=Severity.error, code="unreadable_file", path=rel,
                                    message=f"Cannot read item file as UTF-8: {exc}"))
            continue

        try:
            data = load_yaml(text)
        except yaml.YAMLError as exc:
            findings.append(Finding(severity=Severity.error, code="invalid_yaml", path=rel,
                                    message=f"Invalid YAML: {exc}"))
            continue
        if not isinstance(data, dict):
            findings.append(Finding(severity=Severity.error, code="invalid_yaml", path=rel,
                                    message="Item file is not a YAML mapping"))
            continue

        recoverable_id = data["id"] if isinstance(data.get("id"), str) else None

        try:
            item = Item.model_validate(data)
        except ValidationError as exc:
            for err in exc.errors():
                findings.append(_finding_from_pydantic(err, path=rel, item_id=recoverable_id))
            if recoverable_id is not None:
                paths_by_id[recoverable_id].append(rel)
            continue

        if item.id != filename_id:
            findings.append(Finding(
                severity=Severity.error, code="id_filename_mismatch", path=rel,
                field="id", item_id=item.id,
                message=f"Item id {item.id!r} does not match filename {file.name!r}",
            ))
        paths_by_id[item.id].append(rel)
        status_by_id[item.id] = item.status
        valid_items.append((item, rel))

    # Duplicate IDs: flag every offending file.
    for item_id, rels in paths_by_id.items():
        if len(rels) > 1:
            for rel in rels:
                findings.append(Finding(
                    severity=Severity.error, code="duplicate_id", path=rel, item_id=item_id,
                    message=f"Duplicate item id {item_id!r} (also in {len(rels) - 1} other file(s))",
                ))

    known_ids = set(paths_by_id)

    def _check_reference(target: str, *, rel: str, source_id: str, field: str) -> None:
        if target not in known_ids:
            findings.append(Finding(
                severity=Severity.error, code="missing_reference", path=rel, field=field,
                item_id=source_id, message=f"{field} references unknown item: {target}",
            ))
        elif status_by_id.get(target) == "deleted":
            findings.append(Finding(
                severity=Severity.warning, code="link_to_deleted", path=rel, field=field,
                item_id=source_id, message=f"{field} references deleted item: {target}",
            ))

    for item, rel in valid_items:
        if item.parent_id:
            _check_reference(item.parent_id, rel=rel, source_id=item.id, field="parent_id")
        if item.links:
            for target in item.links.blocks:
                _check_reference(target, rel=rel, source_id=item.id, field="links.blocks")
            for target in item.links.relates_to:
                _check_reference(target, rel=rel, source_id=item.id, field="links.relates_to")
        for attachment in item.attachments or []:
            finding = _validate_attachment(attachment, paths=paths, path=rel, item_id=item.id)
            if finding is not None:
                findings.append(finding)

    findings.extend(_validate_comments(paths))

    findings.sort(key=lambda f: (f.path, f.code, f.field or "", f.message))
    return ValidationReport(findings=findings)
