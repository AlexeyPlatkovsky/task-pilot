"""Unit tests for the deterministic item YAML writer (task F001-T4, F001-R3).

Covers scenario F001-S3: write -> read -> write is byte-identical, plus canonical
field order, omission of absent optionals, and deterministic placement of
preserved unknown fields.
"""

from pathlib import Path

import pytest

from taskpilot.core.item_io import (
    dump_item,
    parse_item_file,
    parse_item_text,
    write_item,
)
from taskpilot.core.layout import WorkspacePaths

FULL_ITEM = """\
schema_version: 1
id: TP-1
title: Benchmark task
priority: high
type: task
status: in_progress
created_at: 2026-06-23T10:00:00Z
updated_at: 2026-06-24T11:00:00Z
parent_id: TP-0
tags:
  - perf
description: A measured task.
attachments:
  - docs/mockup.png
dor:
  - Parent item is clear.
dod:
  - Tests pass.
links:
  blocks:
    - TP-9
  relates_to:
    - TP-12
created_by: Aleksei
performed_by: Bob
external_refs:
  - JIRA-456
"""

MINIMAL_ITEM = """\
schema_version: 1
id: TP-2
title: Minimal
type: bug
status: backlog
created_at: 2026-06-23T10:00:00Z
updated_at: 2026-06-23T10:00:00Z
"""


def _top_level_keys(text: str) -> list[str]:
    return [
        ln.split(":", 1)[0]
        for ln in text.splitlines()
        if ln and not ln[0].isspace() and ":" in ln
    ]


def test_full_item_dumps_in_canonical_field_order():
    text = dump_item(parse_item_text(FULL_ITEM))

    assert _top_level_keys(text) == [
        "schema_version",
        "id",
        "title",
        "priority",
        "type",
        "status",
        "created_at",
        "updated_at",
        "parent_id",
        "tags",
        "description",
        "attachments",
        "dor",
        "dod",
        "links",
        "created_by",
        "performed_by",
        "external_refs",
    ]


def test_minimal_item_omits_absent_optionals():
    text = dump_item(parse_item_text(MINIMAL_ITEM))
    keys = _top_level_keys(text)

    assert keys == [
        "schema_version",
        "id",
        "title",
        "priority",
        "type",
        "status",
        "created_at",
        "updated_at",
    ]
    assert "parent_id" not in text
    assert "null" not in text


def test_write_read_write_is_byte_identical_full():
    first = dump_item(parse_item_text(FULL_ITEM))
    second = dump_item(parse_item_text(first))
    assert first == second


def test_write_read_write_is_byte_identical_minimal():
    first = dump_item(parse_item_text(MINIMAL_ITEM))
    second = dump_item(parse_item_text(first))
    assert first == second


def test_empty_link_lists_are_omitted():
    text = MINIMAL_ITEM + "links:\n  blocks:\n    - TP-9\n"
    dumped = dump_item(parse_item_text(text))

    assert "blocks" in dumped
    assert "relates_to" not in dumped  # default empty list dropped


def test_item_without_any_links_omits_links_key():
    assert "links" not in dump_item(parse_item_text(MINIMAL_ITEM))


def test_unknown_fields_written_after_known_fields_sorted():
    text = MINIMAL_ITEM + "zeta: 1\nalpha: 2\n"
    keys = _top_level_keys(dump_item(parse_item_text(text)))

    assert keys[-2:] == ["alpha", "zeta"]  # extras sorted, after known fields
    assert keys.index("updated_at") < keys.index("alpha")


def test_write_item_persists_to_canonical_path(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    paths.items_dir.mkdir(parents=True)
    item = parse_item_text(MINIMAL_ITEM)

    written = write_item(paths, item)

    assert written == paths.item_file("TP-2")
    assert parse_item_file(written).id == "TP-2"


def test_write_item_creates_missing_items_dir(tmp_path: Path):
    paths = WorkspacePaths.for_root(tmp_path)
    item = parse_item_text(MINIMAL_ITEM)

    written = write_item(paths, item)

    assert written.is_file()


def test_null_valued_unknown_field_is_preserved():
    text = MINIMAL_ITEM + "mystery: null\n"
    dumped = dump_item(parse_item_text(text))

    assert "mystery" in dumped
    assert parse_item_text(dumped).model_extra == {"mystery": None}


def test_explicit_empty_links_normalizes_and_round_trips():
    text = MINIMAL_ITEM + "links:\n  blocks: []\n  relates_to: []\n"
    first = dump_item(parse_item_text(text))
    second = dump_item(parse_item_text(first))

    assert "links" not in first  # empty link lists carry no information
    assert first == second


def test_unicode_round_trips_byte_identically():
    text = MINIMAL_ITEM.replace("title: Minimal", "title: Café — naïve 日本語")
    first = dump_item(parse_item_text(text))
    second = dump_item(parse_item_text(first))

    assert "Café — naïve 日本語" in first
    assert first == second


def test_round_trip_from_model_preserves_fields():
    item = parse_item_text(FULL_ITEM)
    reparsed = parse_item_text(dump_item(item))
    assert reparsed == item


def test_write_item_preserves_existing_file_on_replace_failure(
    tmp_path: Path, monkeypatch
):
    """Existing item file is not truncated if os.replace fails after temp write."""
    paths = WorkspacePaths.for_root(tmp_path)
    paths.items_dir.mkdir(parents=True)
    item = parse_item_text(MINIMAL_ITEM)
    write_item(paths, item)
    item_path = paths.item_file("TP-2")
    original = item_path.read_text(encoding="utf-8")

    def _fail_replace(src: str, dst: str) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr("os.replace", _fail_replace)

    item.title = "Changed"
    with pytest.raises(OSError):
        write_item(paths, item)

    assert item_path.read_text(encoding="utf-8") == original
    assert not list(item_path.parent.glob("*.tmp")), (
        "orphaned temp file after replace failure"
    )


def test_write_item_cleans_up_temp_file_on_write_failure(tmp_path: Path, monkeypatch):
    """Temp file is removed and original preserved if os.write fails."""
    paths = WorkspacePaths.for_root(tmp_path)
    paths.items_dir.mkdir(parents=True)
    item = parse_item_text(MINIMAL_ITEM)
    write_item(paths, item)
    item_path = paths.item_file("TP-2")
    original = item_path.read_text(encoding="utf-8")

    def _fail_write(fd: int, data: bytes) -> int:
        raise OSError("simulated write failure")

    monkeypatch.setattr("os.write", _fail_write)

    item.title = "Changed"
    with pytest.raises(OSError):
        write_item(paths, item)

    assert item_path.read_text(encoding="utf-8") == original
    assert not list(item_path.parent.glob("*.tmp")), (
        "orphaned temp file after write failure"
    )
