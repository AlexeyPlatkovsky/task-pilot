"""Comment domain service: add, list (task F002-T6, requirement F002-R6).

Comments are append-only Markdown files under ``comments/<item_id>/``; the
filename timestamp is the comment identity. Adding a comment never touches the
item YAML. This service wraps the F001 comment primitives with domain rules:
the target item must exist, and low-level parse/validation failures surface as
:class:`ValidationFailed`.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from taskpilot.core import comments as core_comments
from taskpilot.core.comments import Comment, CommentParseError
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.timestamps import utc_now_iso
from taskpilot.services.errors import NotFound, ValidationFailed

__all__ = ["add_comment", "list_comments"]


def add_comment(
    paths: WorkspacePaths,
    item_id: str,
    *,
    body: str,
    created_by: str,
    now: str | None = None,
) -> Path:
    """Add a comment to ``item_id`` and return the written file path (F002-R6).

    A comment's identity *is* its filename (spec ``0002``), so the path — not the
    in-memory model — is the useful result for callers such as the CLI, matching
    the core ``write_comment`` contract. The owning item must exist; a timestamped
    ``.md`` file is written (same-second collisions get ``-N`` suffixes) and the
    item YAML is left untouched. Raises :class:`NotFound` for an unknown item and
    :class:`ValidationFailed` for invalid comment fields (e.g. empty author).
    """
    if not paths.item_file(item_id).is_file():
        raise NotFound(f"No item found with id {item_id!r}")
    try:
        comment = Comment(
            created_at=now or utc_now_iso(), created_by=created_by, body=body
        )
    except ValidationError as exc:
        raise ValidationFailed(f"Cannot add comment to {item_id!r}: {exc}") from exc
    return core_comments.write_comment(paths, item_id, comment)


def list_comments(paths: WorkspacePaths, item_id: str) -> list[Comment]:
    """List ``item_id``'s comments ordered chronologically (F002-R6).

    Returns an empty list when the item has no comments. Raises
    :class:`ValidationFailed` if a stored comment file is malformed.
    """
    try:
        return core_comments.list_comments(paths, item_id)
    except (CommentParseError, ValidationError) as exc:
        raise ValidationFailed(f"Invalid comment for {item_id!r}: {exc}") from exc
