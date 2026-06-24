"""Project loader that separates valid items from validation errors (task F001-T8).

Loading is fault-tolerant (F001-R7): structurally valid items load and are
returned even when sibling files are invalid, and every problem is surfaced
through the :class:`~taskpilot.core.validation.ValidationReport` rather than
crashing or being silently dropped.

The authoritative findings come from :func:`validate_workspace`; this loader adds
the parsed item objects (so callers get usable data) and project-metadata
findings.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from taskpilot.core.item_io import ItemParseError, parse_item_file
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item
from taskpilot.core.project import ProjectMeta, read_project
from taskpilot.core.validation import Finding, Severity, ValidationReport, validate_workspace

__all__ = ["LoadedProject", "load_project"]


class LoadedProject(BaseModel):
    """Result of loading a project: metadata, the parsed items, and all findings.

    ``items`` contains every *structurally parseable* item (sorted by numeric id).
    An item can be structurally valid yet still carry cross-file error findings
    (e.g. ``duplicate_id`` or ``id_filename_mismatch``), so it appears in ``items``
    while ``ok`` is ``False``. ``items`` is therefore not a pre-filtered "valid and
    listable" set; adapters (CLI/WebUI) apply listability rules such as
    deleted-exclusion and the invalid marker, correlating items with ``report`` by
    id/path.
    """

    project: ProjectMeta | None
    items: list[Item]
    report: ValidationReport

    @property
    def ok(self) -> bool:
        return self.report.ok


def _numeric_id_key(item: Item) -> tuple[int, str]:
    """Sort key for items by trailing numeric id suffix (``TP-2`` before ``TP-10``)."""
    _, _, suffix = item.id.rpartition("-")
    return (int(suffix), item.id) if suffix.isdigit() else (-1, item.id)


def load_project(paths: WorkspacePaths) -> LoadedProject:
    """Load a project's items and validation report without crashing on bad files."""
    report = validate_workspace(paths)
    findings: list[Finding] = list(report.findings)

    # Project metadata: surface a finding when missing or invalid, but keep loading.
    project: ProjectMeta | None = None
    project_rel = paths.relative_posix(paths.project_file)
    if not paths.project_file.exists():
        findings.append(Finding(severity=Severity.error, code="project_missing", path=project_rel,
                                message="Project file project.yaml is missing"))
    else:
        try:
            project = read_project(paths)
        except (ValidationError, yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
            findings.append(Finding(severity=Severity.error, code="project_invalid", path=project_rel,
                                    message=f"Invalid project.yaml: {exc}"))

    # Parse the structurally valid items; invalid files are already in the report.
    items: list[Item] = []
    if paths.items_dir.is_dir():
        for file in sorted(p for p in paths.items_dir.glob("*.yaml") if p.is_file()):
            try:
                items.append(parse_item_file(file))
            except (ItemParseError, ValidationError, UnicodeDecodeError, OSError):
                continue
    items.sort(key=_numeric_id_key)

    findings.sort(key=lambda f: (f.path, f.code, f.field or "", f.message))
    return LoadedProject(project=project, items=items, report=ValidationReport(findings=findings))
