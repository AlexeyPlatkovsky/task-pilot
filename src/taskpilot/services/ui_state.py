"""Per-machine WebUI state persisted as ``ui-state.yaml`` (task F010-T5).

Stored in the same OS application-data directory as ``registry.yaml`` and
honors the ``TASKPILOT_HOME`` override. The file is never written under
``.taskpilot/`` and never changes canonical task files.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from taskpilot.core.yaml_io import dump_yaml, load_yaml
from taskpilot.services.registry import default_registry_dir

__all__ = [
    "UI_STATE_FILENAME",
    "UIState",
    "DEFAULT_UI_STATE",
    "ui_state_file",
    "load_ui_state",
    "save_ui_state",
]

UI_STATE_FILENAME = "ui-state.yaml"


class UIState(BaseModel):
    """Per-machine WebUI state.

    ``last_opened_project_id`` stores the registry ``id`` of the last
    explicitly selected project so the WebUI can restore it on startup.
    ``null`` means no project is remembered.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    last_opened_project_id: str | None = None


DEFAULT_UI_STATE = UIState()


def ui_state_file() -> Path:
    """Resolve the full path to ``ui-state.yaml``."""
    return default_registry_dir() / UI_STATE_FILENAME


def load_ui_state() -> UIState:
    """Read ``ui-state.yaml``, returning defaults when absent or unreadable.

    Never raises; a missing, empty, or malformed file is treated as the
    default (empty) UI state so the WebUI always has a usable fallback.
    """
    path = ui_state_file()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return DEFAULT_UI_STATE
    if not text.strip():
        return DEFAULT_UI_STATE
    try:
        data = load_yaml(text)
    except Exception:
        return DEFAULT_UI_STATE
    try:
        return UIState.model_validate(data)
    except Exception:
        return DEFAULT_UI_STATE


def save_ui_state(state: UIState) -> None:
    """Atomically write ``ui-state.yaml``.

    Uses the same tempfile + atomic rename pattern as the registry so
    concurrent readers never see a partial file.
    """
    path = ui_state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = dump_yaml(state.model_dump())
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), prefix="ui-state-", suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
