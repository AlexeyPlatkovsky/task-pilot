"""Unit tests for the comment file writer (task F001-T6, F001-R5).

Covers scenario F001-S5: timestamp-based filenames and same-second collision
disambiguation (-2, -3), with created_at frontmatter matching the filename.
"""

from pathlib import Path

from taskpilot.core.comments import (
    Comment,
    add_comment,
    dump_comment,
    list_comments,
    parse_comment_text,
    write_comment,
)
from taskpilot.core.layout import WorkspacePaths

AT = "2026-06-23T10:00:00Z"


def _comment(body="A note.", created_by="Aleksei", created_at=AT) -> Comment:
    return Comment(created_at=created_at, created_by=created_by, body=body)


def test_write_comment_names_file_from_created_at(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    written = write_comment(paths, "TP-1", _comment())

    assert written.name == "2026-06-23T10-00-00Z.md"
    assert written == paths.item_comments_dir("TP-1") / "2026-06-23T10-00-00Z.md"


def test_write_comment_round_trips_through_parser(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    original = _comment(body="Line one.\n\n- a\n- b")

    written = write_comment(paths, "TP-1", original)

    assert parse_comment_text(written.read_text(encoding="utf-8")) == original


def test_same_second_collisions_get_numeric_suffixes(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)

    n1 = write_comment(paths, "TP-1", _comment(created_by="First"))
    n2 = write_comment(paths, "TP-1", _comment(created_by="Second"))
    n3 = write_comment(paths, "TP-1", _comment(created_by="Third"))

    assert n1.name == "2026-06-23T10-00-00Z.md"
    assert n2.name == "2026-06-23T10-00-00Z-2.md"
    assert n3.name == "2026-06-23T10-00-00Z-3.md"


def test_collisions_stay_chronological_past_nine(tmp_path: Path):
    # Guards the -10 lexical-sort hazard: 12 same-second comments must list in
    # creation order, not lexical filename order.
    paths = WorkspacePaths.for_root(tmp_path)
    for i in range(12):
        write_comment(paths, "TP-1", _comment(created_by=f"c{i:02d}"))

    assert [c.created_by for c in list_comments(paths, "TP-1")] == [f"c{i:02d}" for i in range(12)]


def test_collision_frontmatter_created_at_matches_canonical_timestamp(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    write_comment(paths, "TP-1", _comment())
    second = write_comment(paths, "TP-1", _comment())

    assert parse_comment_text(second.read_text(encoding="utf-8")).created_at == AT


def test_dump_comment_has_frontmatter_then_body():
    text = dump_comment(_comment(body="Body text."))

    assert text.startswith("---\n")
    assert "created_by: Aleksei" in text
    assert text.rstrip().endswith("Body text.")


def test_dump_comment_round_trips_with_extras_and_empty_body():
    c = Comment(created_at=AT, created_by="A", body="", mood="curious")
    assert parse_comment_text(dump_comment(c)) == c


def test_dump_comment_frontmatter_field_order():
    text = dump_comment(_comment())
    fm_keys = [
        ln.split(":", 1)[0]
        for ln in text.splitlines()[1:]
        if ln and not ln.startswith("---") and not ln[0].isspace() and ":" in ln
    ][:3]
    assert fm_keys == ["schema_version", "created_at", "created_by"]


def test_add_comment_uses_explicit_now_and_writes(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    written = add_comment(paths, "TP-1", body="Hi", created_by="A", now=AT)

    assert written.name == "2026-06-23T10-00-00Z.md"
    assert parse_comment_text(written.read_text(encoding="utf-8")).body == "Hi"


def test_add_comment_defaults_to_current_utc_time(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    written = add_comment(paths, "TP-1", body="Hi", created_by="A")

    parsed = parse_comment_text(written.read_text(encoding="utf-8"))
    assert written.name.endswith(".md")
    assert parsed.created_at.endswith("Z")


def test_written_comments_list_chronologically(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    add_comment(paths, "TP-1", body="early", created_by="A", now="2026-06-23T10:00:00Z")
    add_comment(paths, "TP-1", body="collision", created_by="B", now="2026-06-23T10:00:00Z")
    add_comment(paths, "TP-1", body="late", created_by="C", now="2026-06-24T09:00:00Z")

    assert [c.created_by for c in list_comments(paths, "TP-1")] == ["A", "B", "C"]


def test_write_comment_does_not_overwrite_preexisting_file(tmp_path: Path):
    """O_EXCL: a file that already exists on disk is never overwritten."""
    paths = WorkspacePaths.for_root(tmp_path)
    target = paths.item_comments_dir("TP-1") / "2026-06-23T10-00-00Z.md"
    target.parent.mkdir(parents=True)
    target.write_text("preexisting content", encoding="utf-8")

    written = write_comment(paths, "TP-1", _comment())

    assert written.name == "2026-06-23T10-00-00Z-2.md"
    assert target.read_text(encoding="utf-8") == "preexisting content"


def test_write_comment_o_excl_handles_multiple_preexisting_slots(tmp_path: Path):
    """O_EXCL skips pre-existing -2 slot and lands on -3 without overwriting."""
    paths = WorkspacePaths.for_root(tmp_path)
    directory = paths.item_comments_dir("TP-1")
    directory.mkdir(parents=True)

    (directory / "2026-06-23T10-00-00Z.md").write_text("orig", encoding="utf-8")
    (directory / "2026-06-23T10-00-00Z-2.md").write_text("collision", encoding="utf-8")

    written = write_comment(paths, "TP-1", _comment())

    assert written.name == "2026-06-23T10-00-00Z-3.md"
    assert (directory / "2026-06-23T10-00-00Z.md").read_text(encoding="utf-8") == "orig"
    assert (directory / "2026-06-23T10-00-00Z-2.md").read_text(encoding="utf-8") == "collision"
