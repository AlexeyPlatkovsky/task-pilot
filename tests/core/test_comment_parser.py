"""Unit tests for the comment Markdown parser (task F001-T5, F001-R4).

Covers scenario F001-S4 (frontmatter + body extraction) and the chronological
listing requirement, including correct ordering of same-second collision files.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from taskpilot.core.comments import (
    CommentParseError,
    list_comments,
    parse_comment_file,
    parse_comment_text,
)
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.timestamps import filename_stamp_to_iso

COMMENT = """\
---
schema_version: 1
created_at: 2026-06-23T10:00:00Z
created_by: Aleksei
---

Investigated current parser behavior.
"""


def test_parses_frontmatter_and_body():
    c = parse_comment_text(COMMENT)

    assert c.schema_version == 1
    assert c.created_at == "2026-06-23T10:00:00Z"
    assert c.created_by == "Aleksei"
    assert c.body == "Investigated current parser behavior."


def test_preserves_multiline_markdown_body():
    text = COMMENT.replace(
        "Investigated current parser behavior.",
        "Line one.\n\n- bullet\n- bullet two",
    )
    assert parse_comment_text(text).body == "Line one.\n\n- bullet\n- bullet two"


def test_unknown_frontmatter_fields_preserved():
    text = COMMENT.replace("created_by: Aleksei\n", "created_by: Aleksei\nmood: curious\n")
    assert parse_comment_text(text).model_extra == {"mood": "curious"}


def test_missing_frontmatter_raises():
    with pytest.raises(CommentParseError):
        parse_comment_text("Just a body, no frontmatter.\n")


def test_invalid_yaml_frontmatter_raises():
    with pytest.raises(CommentParseError):
        parse_comment_text("---\nfoo: : bad\n---\nbody\n")


def test_non_mapping_frontmatter_raises():
    with pytest.raises(CommentParseError):
        parse_comment_text("---\n- a\n- b\n---\nbody\n")


def test_malformed_created_at_raises_validation_error():
    with pytest.raises(ValidationError):
        parse_comment_text(COMMENT.replace("2026-06-23T10:00:00Z", "whenever"))


def test_missing_created_by_raises_validation_error():
    with pytest.raises(ValidationError):
        parse_comment_text(COMMENT.replace("created_by: Aleksei\n", ""))


def test_parse_comment_file_includes_path_on_error(tmp_path: Path):
    bad = tmp_path / "2026-06-23T10-00-00Z.md"
    bad.write_text("no frontmatter here\n", encoding="utf-8")
    with pytest.raises(CommentParseError) as exc:
        parse_comment_file(bad)
    assert "2026-06-23T10-00-00Z.md" in str(exc.value)


def _write_comment(paths: WorkspacePaths, item_id: str, filename: str, created_at: str, who: str):
    d = paths.item_comments_dir(item_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / filename).write_text(
        f"---\nschema_version: 1\ncreated_at: {created_at}\ncreated_by: {who}\n---\n\n{who}'s note.\n",
        encoding="utf-8",
    )


def test_list_comments_chronological_including_collisions(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    # Intentionally create out of order; collision base + suffixed at the same second.
    _write_comment(paths, "TP-1", "2026-06-24T09-00-00Z.md", "2026-06-24T09:00:00Z", "Later")
    _write_comment(paths, "TP-1", "2026-06-23T10-00-00Z-2.md", "2026-06-23T10:00:00Z", "Second")
    _write_comment(paths, "TP-1", "2026-06-23T10-00-00Z.md", "2026-06-23T10:00:00Z", "First")

    comments = list_comments(paths, "TP-1")

    assert [c.created_by for c in comments] == ["First", "Second", "Later"]


def test_list_comments_empty_when_no_directory(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    assert list_comments(paths, "TP-1") == []


def test_well_formed_comment_created_at_matches_filename_stamp(tmp_path: Path):
    # Scenario F001-S4 happy path: in a valid file, created_at equals the
    # timestamp encoded in the filename.
    name = "2026-06-23T10-00-00Z.md"
    f = tmp_path / name
    f.write_text(COMMENT, encoding="utf-8")

    assert parse_comment_file(f).created_at == filename_stamp_to_iso(name[:-3])


def test_crlf_line_endings_parse_like_lf():
    c = parse_comment_text(COMMENT.replace("\n", "\r\n"))

    assert c.created_by == "Aleksei"
    assert c.body == "Investigated current parser behavior."


def test_parser_does_not_cross_check_filename_against_created_at(tmp_path: Path):
    # Filename/created_at mismatch is a validation-layer concern (F001-T7), so
    # the parser accepts it rather than failing here.
    f = tmp_path / "2099-01-01T00-00-00Z.md"
    f.write_text(COMMENT, encoding="utf-8")
    assert parse_comment_file(f).created_at == "2026-06-23T10:00:00Z"


def test_list_comments_is_strict_and_raises_on_invalid_file(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    _write_comment(paths, "TP-1", "2026-06-23T10-00-00Z.md", "2026-06-23T10:00:00Z", "Valid")
    (paths.item_comments_dir("TP-1") / "2026-06-24T09-00-00Z.md").write_text(
        "no frontmatter\n", encoding="utf-8"
    )
    with pytest.raises(CommentParseError):
        list_comments(paths, "TP-1")
