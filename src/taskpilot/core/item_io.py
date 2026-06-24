"""Reading and writing canonical item YAML files.

F001-T3 implements strict parsing into the :class:`~taskpilot.core.models.Item`
model. YAML syntax problems and non-mapping documents raise :class:`ItemParseError`
with the offending path; schema problems raise pydantic ``ValidationError``.
Both are surfaced as actionable findings by the validation/loader layers
(F001-T7/T8) rather than crashing a project load.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from taskpilot.core.models import Item
from taskpilot.core.yaml_io import load_yaml

__all__ = ["ItemParseError", "parse_item_text", "parse_item_file"]


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
