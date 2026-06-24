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


class _CanonicalLoader(yaml.SafeLoader):
    """SafeLoader that does not auto-convert ISO timestamps to ``datetime``.

    TaskPilot owns canonical timestamp formatting and stores timestamps as
    strings, so implicit timestamp resolution would corrupt round-trip fidelity.
    """


_CanonicalLoader.yaml_implicit_resolvers = {
    first_char: [
        (tag, regexp)
        for tag, regexp in resolvers
        if tag != "tag:yaml.org,2002:timestamp"
    ]
    for first_char, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


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
    """Parse YAML ``text`` into Python data using the canonical safe loader.

    ISO timestamps are kept as strings (see :class:`_CanonicalLoader`).
    """
    return yaml.load(text, Loader=_CanonicalLoader)
