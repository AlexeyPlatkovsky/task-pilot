"""Periodic archive scheduler for server mode (feature F009, task TP-110).

Runs roughly every 3 hours, scanning for eligible items and archiving them.
Only active in long-running server mode; CLI foreground mode has no scheduler.
"""

from __future__ import annotations

import asyncio
import logging

from taskpilot.core.layout import WorkspacePaths
from taskpilot.services import archive_service

__all__ = ["start_archive_scheduler", "stop_archive_scheduler"]

logger = logging.getLogger(__name__)

#: Interval between archive checks (seconds). ~3 hours.
_ARCHIVE_INTERVAL = 3 * 3600  # 10800 seconds

_scheduler_tasks: dict[str, asyncio.Task] = {}


def start_archive_scheduler(workspace_path: str) -> None:
    """Start the periodic archive scheduler.

    Only active in long-running server mode. CLI foreground mode has no scheduler.
    """
    workspace_path = str(WorkspacePaths.for_root(workspace_path).root.resolve())
    if workspace_path in _scheduler_tasks:
        return

    async def _archive_loop() -> None:
        """Main scheduler loop."""
        paths = WorkspacePaths.for_root(workspace_path)
        while True:
            try:
                eligible = archive_service.scan_eligible_items(paths)
                if eligible:
                    item_ids = [item.id for item in eligible]
                    archived = archive_service.archive_items(paths, item_ids)
                    if archived:
                        logger.info(
                            "Archived %d item(s): %s",
                            len(archived),
                            ", ".join(archived),
                        )
                await asyncio.sleep(_ARCHIVE_INTERVAL)
            except Exception as e:
                logger.error("Archive scheduler error: %s", e)
                await asyncio.sleep(_ARCHIVE_INTERVAL)

    _scheduler_tasks[workspace_path] = asyncio.create_task(_archive_loop())


def stop_archive_scheduler() -> None:
    """Stop the periodic archive scheduler."""
    for task in _scheduler_tasks.values():
        task.cancel()
    _scheduler_tasks.clear()
