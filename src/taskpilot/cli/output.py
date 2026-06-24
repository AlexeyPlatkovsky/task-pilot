"""Output formatting for the TaskPilot CLI (task F003-T1, requirement F003-R8).

Two output modes share one rendering seam so every command stays consistent:

- **JSON mode** (``--json``): :func:`dumps_json` serializes plain data to
  deterministic JSON on stdout. Determinism (F003-R8) comes from preserving the
  data's own key order — domain models are dumped in canonical field order, so
  re-running a read command with no state change yields byte-identical bytes. We
  never ``sort_keys``: canonical order is declared field order, not alphabetical.
- **Human mode** (default): helpers render tables, key/value blocks, and
  one-line confirmations to stdout.

Errors always go to stderr (see :mod:`taskpilot.cli.errors`); these helpers
write only success output to stdout.
"""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

__all__ = [
    "dumps_json",
    "print_json",
    "print_line",
    "render_table",
    "render_key_values",
]


def dumps_json(data: Any) -> str:
    """Serialize ``data`` to deterministic, human-readable JSON.

    Key order is taken from ``data`` as given (no ``sort_keys``) so that callers
    controlling field order — e.g. Pydantic ``model_dump`` in canonical order —
    get stable output. Uses 2-space indentation and keeps non-ASCII characters
    verbatim. No trailing newline is added; :func:`print_json` adds one.
    """
    return json.dumps(data, indent=2, ensure_ascii=False)


def print_json(data: Any, *, stream: TextIO | None = None) -> None:
    """Write ``data`` as JSON plus a trailing newline to stdout (or ``stream``)."""
    print(dumps_json(data), file=stream or sys.stdout)


def print_line(text: str, *, stream: TextIO | None = None) -> None:
    """Write a single human-readable line to stdout (or ``stream``)."""
    print(text, file=stream or sys.stdout)


def render_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a fixed-width text table with left-aligned, space-padded columns.

    Returns the header row, a dashed rule, and one line per row. With no rows the
    header and rule are still returned so the column shape is visible.
    """
    columns = [headers] + rows
    widths = [
        max(len(str(row[i])) for row in columns) for i in range(len(headers))
    ]

    def _format(cells: list[str]) -> str:
        return "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(cells)).rstrip()

    lines = [_format(headers), "  ".join("-" * w for w in widths).rstrip()]
    lines.extend(_format(row) for row in rows)
    return "\n".join(lines)


def render_key_values(pairs: list[tuple[str, str]]) -> str:
    """Render ``(key, value)`` pairs as right-padded ``key: value`` lines."""
    if not pairs:
        return ""
    width = max(len(key) for key, _ in pairs)
    return "\n".join(f"{key.ljust(width)}  {value}" for key, value in pairs)
