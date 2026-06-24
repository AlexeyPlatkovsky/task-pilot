"""Workspace layout constants and path resolution for the ``.taskpilot/`` tree.

This module is the storage foundation for feature F001 (task F001-T1). Every
other storage task (parser, writer, validator, project loader) resolves
canonical file locations through :class:`WorkspacePaths` rather than hard-coding
path fragments.

Canonical layout (see ``docs/specs/0002-alpha-product-and-stack-decisions.md``)::

    repo-root/
      .taskpilot/
        project.yaml
        items/
          TP-1.yaml
        comments/
          TP-1/
            2026-06-23T10-00-00Z.md

This module only resolves and validates paths. It does not touch the filesystem
except for :meth:`WorkspacePaths.exists`, and it never reads, writes, or creates
canonical files — that belongs to later tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "WORKSPACE_DIRNAME",
    "PROJECT_FILENAME",
    "ITEMS_DIRNAME",
    "COMMENTS_DIRNAME",
    "ITEM_FILE_SUFFIX",
    "COMMENT_FILE_SUFFIX",
    "WorkspacePaths",
]

#: Repository-local directory that holds all canonical TaskPilot data.
WORKSPACE_DIRNAME = ".taskpilot"
#: Canonical project identity file inside the workspace.
PROJECT_FILENAME = "project.yaml"
#: Directory holding one YAML file per item.
ITEMS_DIRNAME = "items"
#: Directory holding per-item comment folders.
COMMENTS_DIRNAME = "comments"
#: Suffix for canonical item files (``TP-1.yaml``).
ITEM_FILE_SUFFIX = ".yaml"
#: Suffix for canonical comment files (``<timestamp>.md``).
COMMENT_FILE_SUFFIX = ".md"


def _require_safe_segment(value: str, *, kind: str) -> str:
    """Reject values that are empty or would escape their parent directory.

    Path resolution must never let a caller-supplied identifier or filename
    traverse outside the workspace. Item IDs and comment filenames are always
    single path segments, so anything containing a separator or a ``..``
    component is rejected.
    """
    if not value:
        raise ValueError(f"{kind} must not be empty")
    if "/" in value or "\\" in value:
        raise ValueError(f"{kind} must not contain a path separator: {value!r}")
    if value in (".", ".."):
        raise ValueError(f"{kind} must not be a relative traversal segment: {value!r}")
    return value


@dataclass(frozen=True)
class WorkspacePaths:
    """Resolves canonical ``.taskpilot/`` paths relative to a repository root.

    Construct with :meth:`for_root`. Path-returning members never touch the
    filesystem; :meth:`exists` is the only member that reads disk state.
    """

    root: Path

    @classmethod
    def for_root(cls, root: Path | str) -> "WorkspacePaths":
        """Build a resolver for the repository ``root`` that contains ``.taskpilot/``.

        The root is normalized to an absolute path so resolved paths are stable
        regardless of the current working directory.
        """
        return cls(root=Path(root).resolve())

    @property
    def workspace_dir(self) -> Path:
        """The ``.taskpilot/`` directory."""
        return self.root / WORKSPACE_DIRNAME

    @property
    def project_file(self) -> Path:
        """The canonical ``project.yaml`` file."""
        return self.workspace_dir / PROJECT_FILENAME

    @property
    def items_dir(self) -> Path:
        """The ``items/`` directory holding one YAML file per item."""
        return self.workspace_dir / ITEMS_DIRNAME

    @property
    def comments_dir(self) -> Path:
        """The ``comments/`` directory holding per-item comment folders."""
        return self.workspace_dir / COMMENTS_DIRNAME

    def item_file(self, item_id: str) -> Path:
        """Path to the canonical YAML file for ``item_id`` (e.g. ``items/TP-1.yaml``)."""
        _require_safe_segment(item_id, kind="item id")
        return self.items_dir / f"{item_id}{ITEM_FILE_SUFFIX}"

    def item_comments_dir(self, item_id: str) -> Path:
        """Path to the comment folder owned by ``item_id`` (e.g. ``comments/TP-1``)."""
        _require_safe_segment(item_id, kind="item id")
        return self.comments_dir / item_id

    def comment_file(self, item_id: str, filename: str) -> Path:
        """Path to a single comment file under ``item_id``'s comment folder."""
        _require_safe_segment(filename, kind="comment filename")
        return self.item_comments_dir(item_id) / filename

    def relative_posix(self, path: Path) -> str:
        """Render ``path`` relative to the root using ``/`` separators on all platforms.

        Canonical references (validation findings, JSON output) use forward
        slashes regardless of the host OS, e.g. ``.taskpilot/items/TP-1.yaml``.

        Raises :class:`ValueError` when ``path`` is not located under the
        workspace root.
        """
        return path.resolve().relative_to(self.root).as_posix()

    def exists(self) -> bool:
        """True only when the ``.taskpilot/`` workspace directory exists."""
        return self.workspace_dir.is_dir()
