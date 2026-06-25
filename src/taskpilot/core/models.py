"""Canonical item domain models (task F001-T3).

Pydantic models for TaskPilot items, their enums, and non-parent links, matching
``docs/specs/0002`` ("Item Fields", "Item Types", "Statuses", "Priority",
"Links"). Field declaration order is the canonical write order so deterministic
serialization (F001-T4) can rely on it.

Type/enum validation happens here at construction time. Cross-file rules
(unique IDs, id/filename match, reference existence) are validation-layer
concerns (F001-T7), not model concerns.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from typing_extensions import Annotated

from taskpilot.core.timestamps import is_canonical_iso

__all__ = ["SCHEMA_VERSION", "ItemType", "ItemStatus", "Priority", "ItemLinks", "Item"]

#: Current canonical schema version for item files.
SCHEMA_VERSION = 1


class ItemType(str, Enum):
    """Fixed item types through Release."""

    epic = "epic"
    feature = "feature"
    task = "task"
    bug = "bug"


class ItemStatus(str, Enum):
    """Alpha workflow statuses plus the reserved system status ``deleted``."""

    backlog = "backlog"
    ready = "ready"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"
    deleted = "deleted"


class Priority(str, Enum):
    """Item priority; required, defaults to ``normal``."""

    low = "low"
    normal = "normal"
    high = "high"


NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]


class ItemLinks(BaseModel):
    """Non-parent links: a map of link type to target item IDs.

    Alpha supports only ``blocks`` and ``relates_to``; unknown link types (e.g.
    ``duplicates``) are rejected.
    """

    model_config = ConfigDict(extra="forbid")

    blocks: list[str] = Field(default_factory=list)
    relates_to: list[str] = Field(default_factory=list)


class Item(BaseModel):
    """A canonical TaskPilot item.

    Unknown top-level fields are preserved (``extra="allow"``) so updates to
    parseable files do not drop data TaskPilot does not yet model.
    """

    # validate_default ensures defaulted enums (e.g. priority) are coerced to
    # their string values just like supplied ones, so model_dump() never yields a
    # raw enum object that breaks deterministic YAML serialization.
    model_config = ConfigDict(
        extra="allow", use_enum_values=True, validate_default=True
    )

    # Mandatory fields (canonical order first).
    schema_version: int = SCHEMA_VERSION
    id: NonEmptyStr
    title: NonEmptyStr
    priority: Priority = Priority.normal
    type: ItemType
    status: ItemStatus
    created_at: str
    updated_at: str
    # Optional fields, in canonical order. Absent -> None (omitted on write).
    parent_id: str | None = None
    tags: list[str] | None = None
    description: str | None = None
    attachments: list[str] | None = None
    dor: list[str] | None = None
    dod: list[str] | None = None
    links: ItemLinks | None = None
    created_by: str | None = None
    performed_by: str | None = None
    external_refs: list[str] | None = None

    @field_validator("created_at", "updated_at")
    @classmethod
    def _check_timestamp(cls, value: str, info) -> str:
        if not is_canonical_iso(value):
            raise ValueError(
                f"{info.field_name} must be canonical UTC ISO 8601 (YYYY-MM-DDTHH:MM:SSZ): {value!r}"
            )
        return value
