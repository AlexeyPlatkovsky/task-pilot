"""Unit tests for item validation (task F001-T7, F001-R6).

Covers required fields, enums, unique IDs, id/filename match, reference validity
(missing -> error, deleted -> warning), and attachment path safety, all surfaced
as non-crashing findings (scenarios F001-S6, and the F001-R7 spirit that valid
data still validates alongside invalid data).
"""

from pathlib import Path

from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.validation import Severity, validate_workspace

VALID = """\
schema_version: 1
id: {id}
title: {title}
priority: normal
type: task
status: {status}
created_at: 2026-06-23T10:00:00Z
updated_at: 2026-06-23T10:00:00Z
"""


def _write(paths: WorkspacePaths, name: str, text: str):
    paths.items_dir.mkdir(parents=True, exist_ok=True)
    (paths.items_dir / name).write_text(text, encoding="utf-8")


def _item(paths, item_id, *, status="backlog", title="A title", extra=""):
    _write(
        paths,
        f"{item_id}.yaml",
        VALID.format(id=item_id, title=title, status=status) + extra,
    )


def _codes(report):
    return {f.code for f in report.findings}


def test_valid_workspace_reports_ok_and_no_findings(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _item(paths, "TP-1")
    _item(paths, "TP-2")

    report = validate_workspace(paths)

    assert report.ok is True
    assert report.findings == []


def test_missing_title_is_error_with_field_and_path(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _write(
        paths,
        "TP-2.yaml",
        "schema_version: 1\nid: TP-2\ntype: task\nstatus: backlog\n"
        "created_at: 2026-06-23T10:00:00Z\nupdated_at: 2026-06-23T10:00:00Z\n",
    )

    report = validate_workspace(paths)

    assert report.ok is False
    finding = next(f for f in report.findings if f.code == "missing_required_field")
    assert finding.severity == Severity.error
    assert finding.field == "title"
    assert finding.item_id == "TP-2"
    assert finding.path == ".taskpilot/items/TP-2.yaml"
    assert "title" in finding.message


def test_invalid_status_enum_lists_valid_values(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _write(paths, "TP-1.yaml", VALID.format(id="TP-1", title="X", status="imaginary"))

    report = validate_workspace(paths)
    finding = next(f for f in report.findings if f.code == "invalid_enum")

    assert finding.field == "status"
    assert "backlog" in finding.message  # message lists valid statuses


def test_id_filename_mismatch_is_error(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _write(paths, "TP-1.yaml", VALID.format(id="VP-5", title="X", status="backlog"))

    report = validate_workspace(paths)

    assert "id_filename_mismatch" in _codes(report)


def test_duplicate_ids_flag_every_offending_file(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _write(paths, "a.yaml", VALID.format(id="TP-1", title="A", status="backlog"))
    _write(paths, "b.yaml", VALID.format(id="TP-1", title="B", status="backlog"))

    report = validate_workspace(paths)
    dup = [f for f in report.findings if f.code == "duplicate_id"]

    assert {f.path for f in dup} == {
        ".taskpilot/items/a.yaml",
        ".taskpilot/items/b.yaml",
    }


def test_link_to_missing_item_is_error(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _item(paths, "TP-1", extra="links:\n  blocks:\n    - TP-99\n")

    report = validate_workspace(paths)
    finding = next(f for f in report.findings if f.code == "missing_reference")

    assert finding.severity == Severity.error
    assert "TP-99" in finding.message


def test_link_to_deleted_item_is_warning(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _item(paths, "TP-1", extra="links:\n  relates_to:\n    - TP-2\n")
    _item(paths, "TP-2", status="deleted")

    report = validate_workspace(paths)

    assert report.ok is True  # warnings do not flip ok
    finding = next(f for f in report.findings if f.code == "link_to_deleted")
    assert finding.severity == Severity.warning


def test_missing_parent_reference_is_error(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _item(paths, "TP-1", extra="parent_id: TP-404\n")

    report = validate_workspace(paths)
    finding = next(f for f in report.findings if f.code == "missing_reference")

    assert finding.field == "parent_id"


def test_absolute_attachment_is_error(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _item(paths, "TP-1", extra="attachments:\n  - /etc/passwd\n")

    report = validate_workspace(paths)

    assert "attachment_not_relative" in _codes(report)


def test_escaping_attachment_is_error(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _item(paths, "TP-1", extra="attachments:\n  - ../../secret.txt\n")

    report = validate_workspace(paths)

    assert "attachment_outside_repo" in _codes(report)


def test_missing_attachment_file_is_warning(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _item(paths, "TP-1", extra="attachments:\n  - docs/nope.png\n")

    report = validate_workspace(paths)
    finding = next(f for f in report.findings if f.code == "missing_attachment")

    assert finding.severity == Severity.warning
    assert report.ok is True


def test_present_attachment_file_is_ok(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ok.png").write_text("x", encoding="utf-8")
    _item(paths, "TP-1", extra="attachments:\n  - docs/ok.png\n")

    assert validate_workspace(paths).ok is True


def test_unparseable_yaml_is_error_and_does_not_crash(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _write(paths, "TP-1.yaml", "id: TP-1\n  bad: : indent\n")
    _item(paths, "TP-2")  # a valid item still validates alongside

    report = validate_workspace(paths)

    assert "invalid_yaml" in _codes(report)
    assert report.ok is False


def test_non_utf8_file_is_error_and_does_not_crash(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    paths.items_dir.mkdir(parents=True)
    (paths.items_dir / "TP-1.yaml").write_bytes(b"\xff\xfe\x00bad")
    _item(paths, "TP-2")  # valid sibling must still validate

    report = validate_workspace(paths)

    assert "unreadable_file" in _codes(report)
    assert report.ok is False


def test_empty_attachment_path_is_error(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _item(paths, "TP-1", extra="attachments:\n  - ''\n")

    assert "attachment_empty" in _codes(validate_workspace(paths))


def test_findings_are_deterministically_ordered(tmp_path: Path):
    # Locks the CLI/API snapshot contract: findings sort by (path, code, field, message).
    # This file yields id_filename_mismatch (appended early) and attachment_outside_repo
    # (appended later) — their natural build order is the reverse of sorted order, so
    # the assertion fails if the production sort is removed.
    paths = WorkspacePaths.for_root(tmp_path)
    _write(
        paths,
        "TP-1.yaml",
        VALID.format(id="VP-5", title="X", status="backlog")
        + "attachments:\n  - ../../escape.txt\n",
    )

    findings = validate_workspace(paths).findings
    keys = [(f.path, f.code, f.field or "", f.message) for f in findings]

    assert [k[1] for k in keys] == ["attachment_outside_repo", "id_filename_mismatch"]
    assert keys == sorted(keys)


def test_report_to_dict_matches_contract_shape(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _write(
        paths,
        "TP-1.yaml",
        "schema_version: 1\nid: TP-1\ntype: task\nstatus: backlog\n"
        "created_at: 2026-06-23T10:00:00Z\nupdated_at: 2026-06-23T10:00:00Z\n",
    )

    data = validate_workspace(paths).to_dict()

    assert data["ok"] is False
    assert data["summary"] == {"errors": 1, "warnings": 0}
    assert isinstance(data["findings"], list)
    f = data["findings"][0]
    assert set(f) == {"severity", "code", "path", "field", "item_id", "message"}


def test_empty_workspace_is_ok(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    paths.items_dir.mkdir(parents=True)

    report = validate_workspace(paths)

    assert report.ok is True
    assert report.findings == []
