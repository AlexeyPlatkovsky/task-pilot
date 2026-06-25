"""Locate the TaskPilot workspace for repo-scoped commands (task F003-T4).

Commands like ``item`` and ``validate`` operate on "the current project". They
resolve it by walking up from the current directory to the nearest ancestor that
contains a ``.taskpilot/`` directory — the conventional repo-root discovery used
by Git-like tools. ``init`` does not use this (it inspects only the given path).
"""

from __future__ import annotations

from pathlib import Path

from taskpilot.core.layout import WORKSPACE_DIRNAME, WorkspacePaths
from taskpilot.services.errors import NotFound

__all__ = ["find_workspace"]


def find_workspace(start: Path | None = None) -> WorkspacePaths:
    """Return the workspace for the repo containing ``start`` (default: cwd).

    Walks ``start`` and its parents for a ``.taskpilot/`` directory. Raises
    :class:`~taskpilot.services.errors.NotFound` (mapped to exit code 1) when no
    workspace is found, with a hint to run ``taskpilot init``.
    """
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        if (directory / WORKSPACE_DIRNAME).is_dir():
            return WorkspacePaths.for_root(directory)
    raise NotFound(
        f"No TaskPilot workspace found in {current} or any parent directory; "
        "run `taskpilot init .` in the project root"
    )
