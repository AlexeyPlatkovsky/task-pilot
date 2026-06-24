"""Unit tests for comment-file validation (task F001-T9, F001-R7).

validate_workspace also scans .taskpilot/comments/<ITEM_ID>/*.md: malformed or
unreadable comment files become error findings, and a filename whose timestamp
does not match the frontmatter created_at becomes a warning (scenario F001-S4's
"matching" clause). Comment problems never crash the run.
"""

from pathlib import Path

import pytest

from taskpilot.core.comments import comment_filename_timestamp
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.validation import Severity, validate_workspace


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("2026-06-23T10-00-00Z.md", "2026-06-23T10:00:00Z"),
        ("2026-06-23T10-00-00Z-2.md", "2026-06-23T10:00:00Z"),  # collision suffix stripped
        ("2026-06-23T10-00-00Z-10.md", "2026-06-23T10:00:00Z"),
        ("notes.md", None),  # no Z / not a stamp
        ("2026-13-99T99-99-99Z.md", None),  # invalid calendar values
        ("Z.md", None),  # bare Z is not a stamp
    ],
)
def test_comment_filename_timestamp_edge_cases(filename, expected):
    assert comment_filename_timestamp(filename) == expected

GOOD_COMMENT = """\
---
schema_version: 1
created_at: {created_at}
created_by: Aleksei
---

A note.
"""


def _comment(paths: WorkspacePaths, item_id: str, filename: str, created_at: str = "2026-06-23T10:00:00Z", *, raw: str | None = None):
    d = paths.item_comments_dir(item_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / filename).write_text(raw if raw is not None else GOOD_COMMENT.format(created_at=created_at), encoding="utf-8")


def _codes(report):
    return {f.code for f in report.findings}


def test_valid_comment_produces_no_findings(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _comment(paths, "TP-1", "2026-06-23T10-00-00Z.md")

    report = validate_workspace(paths)

    assert report.findings == []
    assert report.ok is True


def test_matching_collision_suffix_filename_is_valid(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _comment(paths, "TP-1", "2026-06-23T10-00-00Z-2.md")  # base stamp still matches created_at

    assert validate_workspace(paths).findings == []


def test_malformed_comment_frontmatter_is_error(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _comment(paths, "TP-1", "2026-06-23T10-00-00Z.md", raw="no frontmatter at all\n")

    report = validate_workspace(paths)
    finding = next(f for f in report.findings if f.code == "invalid_comment")

    assert finding.severity == Severity.error
    assert finding.item_id == "TP-1"
    assert finding.path == ".taskpilot/comments/TP-1/2026-06-23T10-00-00Z.md"
    assert report.ok is False


def test_comment_missing_required_field_is_error(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _comment(paths, "TP-1", "2026-06-23T10-00-00Z.md",
             raw="---\nschema_version: 1\ncreated_at: 2026-06-23T10:00:00Z\n---\n\nbody\n")

    report = validate_workspace(paths)
    finding = next(f for f in report.findings if f.code == "missing_required_field")

    assert finding.field == "created_by"
    assert finding.item_id == "TP-1"


def test_unreadable_comment_file_is_error_and_does_not_crash(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    d = paths.item_comments_dir("TP-1")
    d.mkdir(parents=True)
    (d / "2026-06-23T10-00-00Z.md").write_bytes(b"\xff\xfe\x00bad")
    _comment(paths, "TP-2", "2026-06-24T09-00-00Z.md")  # valid sibling still validates

    report = validate_workspace(paths)

    assert "comment_unreadable" in _codes(report)
    assert report.ok is False


def test_filename_created_at_mismatch_is_warning(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    # Filename says 09:00:00, frontmatter says 10:00:00.
    _comment(paths, "TP-1", "2026-06-23T09-00-00Z.md", created_at="2026-06-23T10:00:00Z")

    report = validate_workspace(paths)
    finding = next(f for f in report.findings if f.code == "comment_timestamp_mismatch")

    assert finding.severity == Severity.warning
    assert finding.field == "created_at"
    assert report.ok is True  # warning does not block


def test_non_timestamp_filename_is_warning(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _comment(paths, "TP-1", "notes.md")

    report = validate_workspace(paths)

    assert "comment_filename_not_timestamp" in _codes(report)
    assert report.ok is True


def test_comment_findings_coexist_with_item_findings(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    paths.items_dir.mkdir(parents=True)
    (paths.items_dir / "TP-1.yaml").write_text(
        "schema_version: 1\nid: TP-1\ntitle: T\npriority: normal\ntype: task\n"
        "status: backlog\ncreated_at: 2026-06-23T10:00:00Z\nupdated_at: 2026-06-23T10:00:00Z\n",
        encoding="utf-8",
    )
    _comment(paths, "TP-1", "2026-06-23T10-00-00Z.md", raw="broken\n")

    report = validate_workspace(paths)

    assert "invalid_comment" in _codes(report)
    # findings stay deterministically sorted
    keys = [(f.path, f.code, f.field or "", f.message) for f in report.findings]
    assert keys == sorted(keys)


def test_no_comments_directory_is_fine(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    paths.items_dir.mkdir(parents=True)

    assert validate_workspace(paths).ok is True
