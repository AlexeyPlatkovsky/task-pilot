"""Deterministic YAML serialization for canonical TaskPilot files.

TaskPilot owns canonical YAML formatting (see ``docs/specs/0002``). Canonical
files are written with a single, stable style so that re-serializing parsed data
is reproducible and Git-friendly. This module centralizes that style; project
and item writers must serialize through :func:`dump_yaml`.
"""

from __future__ import annotations

from typing import Any

import yaml

__all__ = ["dump_yaml", "load_yaml"]


def dump_yaml(data: Any) -> str:
    """Serialize ``data`` to canonical YAML text.

    Key order is preserved (not sorted) so callers control field order; output
    uses block style and allows unicode. The result ends with a single trailing
    newline.
    """
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=4096,
    )


def load_yaml(text: str) -> Any:
    """Parse YAML ``text`` into Python data using the safe loader."""
    return yaml.safe_load(text)
