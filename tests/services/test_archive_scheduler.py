"""Lifecycle tests for per-workspace archive scheduling (TP-131)."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from taskpilot.server import app as server_app
from taskpilot.services import archive_scheduler


class _Task:
    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


def test_starts_one_scheduler_per_distinct_workspace(monkeypatch):
    created: list[str] = []

    def create_task(coroutine):
        created.append(coroutine.cr_frame.f_locals["workspace_path"])
        coroutine.close()
        return _Task()

    monkeypatch.setattr(archive_scheduler, "_scheduler_tasks", {})
    monkeypatch.setattr(archive_scheduler.asyncio, "create_task", create_task)

    archive_scheduler.start_archive_scheduler("/workspace-one/")
    archive_scheduler.start_archive_scheduler("/workspace-two")
    archive_scheduler.start_archive_scheduler("/workspace-one")

    assert created == ["/workspace-one", "/workspace-two"]
    assert set(archive_scheduler._scheduler_tasks) == {
        "/workspace-one",
        "/workspace-two",
    }


def test_stop_cancels_all_workspace_schedulers(monkeypatch):
    first = _Task()
    second = _Task()
    monkeypatch.setattr(
        archive_scheduler,
        "_scheduler_tasks",
        {"/workspace-one": first, "/workspace-two": second},
    )

    archive_scheduler.stop_archive_scheduler()

    assert first.cancelled is True
    assert second.cancelled is True
    assert archive_scheduler._scheduler_tasks == {}


def test_server_starts_schedulers_for_all_active_registered_workspaces(monkeypatch):
    started: list[str] = []
    monkeypatch.setattr(
        "taskpilot.services.registry.list_projects",
        lambda _directory: [
            SimpleNamespace(path="/active-one", active=True),
            SimpleNamespace(path="/active-one/", active=True),
            SimpleNamespace(path="/inactive", active=False),
            SimpleNamespace(path="/active-two", active=True),
        ],
    )
    monkeypatch.setattr(
        archive_scheduler, "start_archive_scheduler", lambda path: started.append(path)
    )
    app = SimpleNamespace(state=SimpleNamespace(registry_dir="/registry"))

    asyncio.run(server_app._startup_logic(app))

    assert started == ["/active-one", "/active-two"]


def test_scheduler_failures_are_isolated_per_workspace(monkeypatch):
    coroutines = []
    archived: list[str] = []

    def create_task(coroutine):
        coroutines.append(coroutine)
        return _Task()

    class StopLoop(BaseException):
        pass

    async def stop_after_iteration(_seconds):
        raise StopLoop()

    def scan(paths):
        if str(paths.root) == "/broken":
            raise OSError("unreadable workspace")
        return [SimpleNamespace(id="TP-1")]

    monkeypatch.setattr(archive_scheduler, "_scheduler_tasks", {})
    monkeypatch.setattr(archive_scheduler.asyncio, "create_task", create_task)
    monkeypatch.setattr(archive_scheduler.asyncio, "sleep", stop_after_iteration)
    monkeypatch.setattr(archive_scheduler.archive_service, "scan_eligible_items", scan)
    monkeypatch.setattr(
        archive_scheduler.archive_service,
        "archive_items",
        lambda paths, _ids: archived.append(str(paths.root)) or ["TP-1"],
    )

    archive_scheduler.start_archive_scheduler("/broken")
    archive_scheduler.start_archive_scheduler("/healthy")

    for coroutine in coroutines:
        with pytest.raises(StopLoop):
            asyncio.run(coroutine)
    assert archived == ["/healthy"]
