"""Centralized pre-write operation validation (task F002-T8, requirement F002-R8).

Services validate operation input here *before* touching the filesystem, so an
invalid operation is rejected with a descriptive error and never leaves a partial
or invalid file on disk. This is the single place that turns low-level pydantic
``ValidationError`` detail into human-readable, field-level messages for the
domain layer; adapters render the resulting :class:`ValidationFailed` message.

Cross-file rules (reference existence, hierarchy, link targets) live in their own
modules (validation layer, :mod:`hierarchy`, :mod:`link_service`); this module
owns single-item field/shape validation that must pass before a write.
"""

from __future__ import annotations

from pydantic import ValidationError

from taskpilot.core.models import Item
from taskpilot.services.errors import ValidationFailed

__all__ = ["describe_validation_error", "build_validated_item"]


def _describe_error(err: dict) -> str:
    """Render one pydantic error as a human-readable field-level message."""
    field = ".".join(str(p) for p in err["loc"])
    etype = err["type"]
    if etype == "missing":
        return f"Missing required field: {field}"
    if etype == "enum":
        expected = err.get("ctx", {}).get("expected", "")
        return f"Invalid value for {field}: expected one of {expected}"
    return f"{field}: {err['msg']}"


def describe_validation_error(exc: ValidationError) -> str:
    """Join all field-level problems in ``exc`` into one descriptive message."""
    return "; ".join(_describe_error(err) for err in exc.errors())


def build_validated_item(data: dict) -> Item:
    """Validate item ``data`` into an :class:`Item`, or raise :class:`ValidationFailed`.

    The raised error carries a descriptive, field-level message so callers never
    need to write a file just to discover the input was invalid (F002-R8).
    """
    try:
        return Item.model_validate(data)
    except ValidationError as exc:
        raise ValidationFailed(
            f"Invalid item: {describe_validation_error(exc)}"
        ) from exc
