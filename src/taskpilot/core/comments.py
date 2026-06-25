"""Comment model and Markdown-with-frontmatter parsing (task F001-T5).

Comments are append-only Markdown files with a YAML frontmatter block::

    ---
    schema_version: 1
    created_at: 2026-06-23T10:00:00Z
    created_by: Aleksei
    ---

    Investigated current parser behavior.

They live under ``.taskpilot/comments/<ITEM_ID>/``; the folder name is the owning
item ID, so frontmatter does not duplicate it. The filename timestamp is the
comment identity and should match ``created_at``. Comment writing and timestamp
collision handling are F001-T6.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from typing_extensions import Annotated

from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.timestamps import (
    filename_stamp_to_iso,
    is_canonical_iso,
    iso_to_filename_stamp,
    utc_now_iso,
)
from taskpilot.core.yaml_io import dump_yaml, load_yaml

__all__ = [
    "SCHEMA_VERSION",
    "Comment",
    "CommentParseError",
    "parse_comment_text",
    "parse_comment_file",
    "list_comments",
    "dump_comment",
    "write_comment",
    "add_comment",
    "comment_filename_timestamp",
]

#: Current canonical schema version for comment frontmatter.
SCHEMA_VERSION = 1

_FRONTMATTER_RE = re.compile(r"\A---\n(?P<fm>.*?)\n---\n?(?P<body>.*)\Z", re.DOTALL)

NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]


class CommentParseError(Exception):
    """Raised when a comment file lacks valid YAML frontmatter or a mapping body."""

    def __init__(self, message: str, *, path: Path | None = None):
        self.path = path
        super().__init__(f"{path}: {message}" if path is not None else message)


class Comment(BaseModel):
    """A single append-only comment parsed from a Markdown file."""

    model_config = ConfigDict(extra="allow")

    schema_version: int = SCHEMA_VERSION
    created_at: str
    created_by: NonEmptyStr
    body: str = ""

    @field_validator("created_at")
    @classmethod
    def _check_created_at(cls, value: str) -> str:
        if not is_canonical_iso(value):
            raise ValueError(
                f"created_at must be canonical UTC ISO 8601 (YYYY-MM-DDTHH:MM:SSZ): {value!r}"
            )
        return value


def parse_comment_text(text: str, *, path: Path | None = None) -> Comment:
    """Parse comment Markdown ``text`` into a :class:`Comment`.

    Raises :class:`CommentParseError` for missing/invalid frontmatter and pydantic
    ``ValidationError`` for schema problems.

    Line endings are normalized to ``\\n`` first, so CRLF files (e.g. produced on
    Windows or by ``core.autocrlf``) parse identically to LF files.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        raise CommentParseError("missing or malformed YAML frontmatter", path=path)
    try:
        data = load_yaml(match.group("fm"))
    except yaml.YAMLError as exc:
        raise CommentParseError(f"invalid YAML frontmatter: {exc}", path=path) from exc
    if not isinstance(data, dict):
        raise CommentParseError("frontmatter is not a mapping", path=path)
    return Comment.model_validate({**data, "body": match.group("body").strip("\n")})


def parse_comment_file(path: Path) -> Comment:
    """Read and parse the comment file at ``path``.

    Note: the filename timestamp is the comment's identity and should match
    ``created_at`` (see ``docs/specs/0002``). For well-formed files they do match;
    the parser does not *enforce* the match (a mismatch is accepted), leaving
    detection to a future comment-validation layer. No F001 task currently owns
    that check.
    """
    return parse_comment_text(path.read_text(encoding="utf-8"), path=path)


def _comment_sort_key(filename: str) -> tuple[str, int]:
    """Chronological sort key ``(timestamp, collision_suffix)`` for a comment filename.

    A base file like ``2026-06-23T10-00-00Z.md`` sorts before its same-second
    collision ``2026-06-23T10-00-00Z-2.md``; raw lexical order would invert them.
    """
    stem = filename[:-3] if filename.endswith(".md") else filename
    marker = stem.find("Z")
    if marker == -1:
        return (stem, 0)
    stamp = stem[: marker + 1]
    rest = stem[marker + 1 :]
    suffix = int(rest.lstrip("-")) if rest.startswith("-") and rest[1:].isdigit() else 0
    return (stamp, suffix)


def comment_filename_timestamp(filename: str) -> str | None:
    """Return the canonical ISO timestamp encoded in a comment filename, or ``None``.

    Strips the ``.md`` suffix and any ``-N`` collision suffix, then converts the
    ``YYYY-MM-DDTHH-MM-SSZ`` stamp to ``YYYY-MM-DDTHH:MM:SSZ``. Returns ``None``
    when the filename does not encode a valid timestamp stamp.
    """
    stem = filename[:-3] if filename.endswith(".md") else filename
    marker = stem.find("Z")
    if marker == -1:
        return None
    try:
        return filename_stamp_to_iso(stem[: marker + 1])
    except ValueError:
        return None


def list_comments(paths: WorkspacePaths, item_id: str) -> list[Comment]:
    """Return ``item_id``'s comments parsed and ordered chronologically.

    Returns an empty list when the item has no comment directory. This is a
    strict accessor: it raises :class:`CommentParseError` (or pydantic
    ``ValidationError``) on the first malformed comment file rather than skipping
    it. Fault-tolerant loading that surfaces invalid files as findings is a
    validation-layer concern (F001-T7); callers needing tolerance should validate
    first.
    """
    directory = paths.item_comments_dir(item_id)
    if not directory.is_dir():
        return []
    files = sorted(
        (p for p in directory.iterdir() if p.is_file() and p.suffix == ".md"),
        key=lambda p: _comment_sort_key(p.name),
    )
    return [parse_comment_file(p) for p in files]


def dump_comment(comment: Comment) -> str:
    """Serialize ``comment`` to Markdown-with-frontmatter, round-tripping the parser.

    Frontmatter is emitted as ``schema_version``, ``created_at``, ``created_by``,
    then preserved unknown fields in sorted key order, followed by the body.
    """
    raw = comment.model_dump()
    frontmatter: dict = {
        "schema_version": raw["schema_version"],
        "created_at": raw["created_at"],
        "created_by": raw["created_by"],
    }
    for key in sorted(k for k in raw if k not in Comment.model_fields):
        frontmatter[key] = raw[key]

    text = f"---\n{dump_yaml(frontmatter)}---\n"
    if comment.body:
        text += f"\n{comment.body}\n"
    return text


def write_comment(paths: WorkspacePaths, item_id: str, comment: Comment) -> Path:
    """Write ``comment`` under ``item_id``, returning the chosen path.

    The filename is derived from ``comment.created_at``; same-second collisions
    receive ``-2``, ``-3``, ... suffixes (F001-R5). Creates the comment directory
    if missing.

    Slot acquisition uses ``open(..., "x")`` (O_EXCL) so the check-and-create is
    atomic: two concurrent writers in the same second cannot both claim the same
    filename.
    """
    directory = paths.item_comments_dir(item_id)
    directory.mkdir(parents=True, exist_ok=True)

    content = dump_comment(comment)
    base = iso_to_filename_stamp(comment.created_at)
    target = directory / f"{base}.md"
    suffix = 2
    while True:
        try:
            with open(target, "x", encoding="utf-8") as f:
                f.write(content)
            return target
        except FileExistsError:
            if suffix > 10_000:
                raise RuntimeError(f"Too many comment collisions for {base}")
            target = directory / f"{base}-{suffix}.md"
            suffix += 1


def add_comment(
    paths: WorkspacePaths,
    item_id: str,
    *,
    body: str,
    created_by: str,
    now: str | None = None,
) -> Path:
    """Create and write a new comment for ``item_id``; returns the written path.

    ``now`` defaults to the current UTC time and becomes both the frontmatter
    ``created_at`` and the filename timestamp.
    """
    comment = Comment(created_at=now or utc_now_iso(), created_by=created_by, body=body)
    return write_comment(paths, item_id, comment)
