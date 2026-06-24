"""Reading and writing canonical item YAML files.

F001-T3 implements strict parsing into the :class:`~taskpilot.core.models.Item`
model. YAML syntax problems and non-mapping documents raise :class:`ItemParseError`
with the offending path; schema problems raise pydantic ``ValidationError``.
Both are surfaced as actionable findings by the validation/loader layers
(F001-T7/T8) rather than crashing a project load.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml

from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item
from taskpilot.core.yaml_io import dump_yaml, load_yaml

__all__ = ["ItemParseError", "parse_item_text", "parse_item_file", "dump_item", "write_item"]


class ItemParseError(Exception):
    """Raised when item YAML cannot be read as a mapping document.

    Distinct from pydantic ``ValidationError`` (schema/field problems): this
    covers YAML syntax errors and documents whose top level is not a mapping.
    """

    def __init__(self, message: str, *, path: Path | None = None):
        self.path = path
        super().__init__(f"{path}: {message}" if path is not None else message)


def parse_item_text(text: str, *, path: Path | None = None) -> Item:
    """Parse item YAML ``text`` into an :class:`Item`.

    Raises :class:`ItemParseError` for YAML syntax errors or a non-mapping
    document, and pydantic ``ValidationError`` for schema/field problems.
    """
    try:
        data = load_yaml(text)
    except yaml.YAMLError as exc:
        raise ItemParseError(f"invalid YAML: {exc}", path=path) from exc
    if not isinstance(data, dict):
        raise ItemParseError(
            f"expected a YAML mapping, got {type(data).__name__}", path=path
        )
    return Item.model_validate(data)


def parse_item_file(path: Path) -> Item:
    """Read and parse the item file at ``path``."""
    text = path.read_text(encoding="utf-8")
    return parse_item_text(text, path=path)


def dump_item(item: Item) -> str:
    """Serialize ``item`` to canonical YAML text.

    Known fields are emitted in canonical declaration order; absent optionals
    (``None``) and empty link lists are omitted; preserved unknown fields are
    written after known fields in sorted key order. The result is byte-stable on
    re-serialization (F001-R3).
    """
    raw = item.model_dump()

    ordered: dict = {}
    for name in Item.model_fields:
        if name not in raw:
            continue
        value = raw[name]
        if value is None:
            continue  # absent optional field is omitted
        if name == "links":
            non_empty = {k: v for k, v in value.items() if v}
            if non_empty:
                ordered[name] = non_empty
            continue
        ordered[name] = value

    # Preserve unknown fields verbatim (including explicit nulls), after known
    # fields, in sorted key order.
    for key in sorted(k for k in raw if k not in Item.model_fields):
        ordered[key] = raw[key]

    return dump_yaml(ordered)


def write_item(paths: WorkspacePaths, item: Item) -> Path:
    """Write ``item`` to its canonical ``items/<id>.yaml`` path.

    Creates the ``items/`` directory if missing, serializes the item first, then
    publishes via a temp-file + ``os.replace`` so the target file is never left
    truncated by a partial write.
    """
    target = paths.item_file(item.id)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = dump_item(item).encode("utf-8")
    fd, tmp = tempfile.mkstemp(dir=str(target.parent), prefix=f".{item.id}_", suffix=".tmp")
    try:
        os.write(fd, content)
    except BaseException:
        os.close(fd)
        os.unlink(tmp)
        raise
    os.close(fd)
    try:
        os.replace(tmp, str(target))
    except BaseException:
        os.unlink(tmp)
        raise
    return target
