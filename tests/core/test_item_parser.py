"""Unit tests for item models and the item YAML parser (task F001-T3, F001-R2).

Scope: strict parsing of a single item file into a typed model, including enums,
links, optional fields, and unknown-field preservation. Cross-file validation
(unique IDs, id/filename match, reference validity) is F001-T7; non-crashing
load of mixed valid/invalid items is F001-T8.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from taskpilot.core.item_io import ItemParseError, parse_item_file, parse_item_text
from taskpilot.core.models import ItemStatus, ItemType, Priority

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
  - alpha
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


def test_parses_all_fields_of_a_full_item():
    item = parse_item_text(FULL_ITEM)

    assert item.id == "TP-1"
    assert item.title == "Benchmark task"
    assert item.priority == Priority.high
    assert item.type == ItemType.task
    assert item.status == ItemStatus.in_progress
    assert item.created_at == "2026-06-23T10:00:00Z"
    assert item.updated_at == "2026-06-24T11:00:00Z"
    assert item.parent_id == "TP-0"
    assert item.tags == ["perf", "alpha"]
    assert item.description == "A measured task."
    assert item.attachments == ["docs/mockup.png"]
    assert item.dor == ["Parent item is clear."]
    assert item.dod == ["Tests pass."]
    assert item.links is not None
    assert item.links.blocks == ["TP-9"]
    assert item.links.relates_to == ["TP-12"]
    assert item.created_by == "Aleksei"
    assert item.performed_by == "Bob"
    assert item.external_refs == ["JIRA-456"]


def test_minimal_item_defaults_optionals_to_absent():
    item = parse_item_text(MINIMAL_ITEM)

    assert item.priority == Priority.normal  # required field, defaults to normal
    assert item.parent_id is None
    assert item.tags is None
    assert item.description is None
    assert item.attachments is None
    assert item.links is None
    assert item.external_refs is None


def test_defaulted_priority_serializes_as_plain_string():
    # Regression: a defaulted enum must dump as its string value, not an enum
    # object, so deterministic YAML serialization (F001-T4) does not break.
    item = parse_item_text(MINIMAL_ITEM)
    dumped = item.model_dump(exclude_none=True)

    assert dumped["priority"] == "normal"
    assert type(dumped["priority"]) is str


def test_deleted_is_a_valid_status():
    text = MINIMAL_ITEM.replace("status: backlog", "status: deleted")
    assert parse_item_text(text).status == ItemStatus.deleted


def test_unknown_top_level_fields_are_preserved():
    text = MINIMAL_ITEM + "future_field: keep-me\n"
    item = parse_item_text(text)

    assert item.model_extra == {"future_field": "keep-me"}


def test_missing_required_field_raises_validation_error():
    text = MINIMAL_ITEM.replace("title: Minimal\n", "")
    with pytest.raises(ValidationError):
        parse_item_text(text)


def test_invalid_status_enum_raises_validation_error():
    text = MINIMAL_ITEM.replace("status: backlog", "status: imaginary_status")
    with pytest.raises(ValidationError):
        parse_item_text(text)


def test_invalid_type_enum_raises_validation_error():
    text = MINIMAL_ITEM.replace("type: bug", "type: saga")
    with pytest.raises(ValidationError):
        parse_item_text(text)


def test_malformed_created_at_raises_validation_error():
    text = MINIMAL_ITEM.replace(
        "created_at: 2026-06-23T10:00:00Z", "created_at: yesterday"
    )
    with pytest.raises(ValidationError):
        parse_item_text(text)


def test_unknown_link_type_is_rejected():
    text = MINIMAL_ITEM + "links:\n  duplicates:\n    - TP-3\n"
    with pytest.raises(ValidationError):
        parse_item_text(text)


def test_syntax_error_yaml_raises_item_parse_error(tmp_path: Path):
    bad = tmp_path / "TP-9.yaml"
    bad.write_text("id: TP-9\n  bad: : indent\n", encoding="utf-8")
    with pytest.raises(ItemParseError) as exc:
        parse_item_file(bad)
    assert "TP-9.yaml" in str(exc.value)


def test_non_mapping_yaml_raises_item_parse_error():
    with pytest.raises(ItemParseError):
        parse_item_text("- just\n- a\n- list\n")


def test_parse_item_file_reads_from_disk(tmp_path: Path):
    f = tmp_path / "TP-2.yaml"
    f.write_text(MINIMAL_ITEM, encoding="utf-8")
    assert parse_item_file(f).id == "TP-2"
