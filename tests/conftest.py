"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from taskpilot.services import archive_service

# Fixed clock for archive placement. Archive fixtures use items updated on
# 2026-07-20; this instant is past the default 14-day threshold and inside the
# 2026-08 archive month that those tests assert on.
ARCHIVE_CLOCK = "2026-08-15T12:00:00Z"


@pytest.fixture
def frozen_archive_clock(monkeypatch: pytest.MonkeyPatch) -> str:
    """Pin the archive service's clock so results never depend on the real date.

    Archive eligibility and the ``archived/<YYYY-MM>/`` destination both derive
    from "now" when callers pass no explicit timestamp (CLI and REST adapters).
    """
    monkeypatch.setattr(archive_service, "utc_now_iso", lambda: ARCHIVE_CLOCK)
    return ARCHIVE_CLOCK
