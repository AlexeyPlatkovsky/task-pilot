"""API integration tests for the FastAPI server (task F005-T8).

Covers all endpoints, 404 paths, 422 validation errors, and deterministic
JSON serialization using FastAPI TestClient.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from taskpilot.cli.registry import (
    default_registry_dir,
    register_project as registry_register,
)
from taskpilot.core.layout import WorkspacePaths
from taskpilot.server.app import create_app
from taskpilot.services import item_service, project_service


@pytest.fixture
def app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    monkeypatch.setenv("TASKPILOT_HOME", str(registry_dir))

    app = create_app(
        workspace=str(tmp_path),
        registry_dir=str(registry_dir),
    )
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def workspace(tmp_path: Path) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path)
    project_service.create_project(
        paths, key="VP", name="VoicePilot", now="2026-06-25T10:00:00Z"
    )
    return paths


def _setup_registry(workspace: WorkspacePaths, tmp_path: Path):
    registry_dir = tmp_path / "registry"
    registry_register(
        registry_dir,
        id="voice-pilot",
        key="VP",
        name="VoicePilot",
        path=str(workspace.root),
        now="2026-06-25T10:00:00Z",
    )


class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestListProjects:
    def test_empty_when_no_registry(self, client):
        r = client.get("/api/projects")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_registered_projects(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        r = client.get("/api/projects")
        data = r.json()
        assert len(data) == 1
        assert data[0] == {
            "id": "voice-pilot",
            "key": "VP",
            "name": "VoicePilot",
            "active": True,
        }


class TestListItems:
    def test_list_excludes_deleted(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="Active item",
            type="task",
            now="2026-06-25T10:00:00Z",
        )
        item_service.create_item(
            workspace,
            title="To delete",
            type="bug",
            now="2026-06-25T10:01:00Z",
        )
        item_service.delete_item(workspace, "VP-2", now="2026-06-25T10:02:00Z")

        r = client.get("/api/projects/voice-pilot/items")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["id"] == "VP-1"

    def test_404_for_unknown_project(self, client):
        r = client.get("/api/projects/ghost/items")
        assert r.status_code == 404
        assert r.json() == {"detail": "Project not found: ghost"}

    def test_empty_items_list(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        r = client.get("/api/projects/voice-pilot/items")
        assert r.status_code == 200
        assert r.json() == []


class TestGetItem:
    def test_returns_detail_with_comments(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="My item",
            type="task",
            priority="high",
            now="2026-06-25T10:00:00Z",
        )
        from taskpilot.services.comment_service import add_comment

        add_comment(
            workspace,
            "VP-1",
            body="First comment",
            created_by="Tester",
            now="2026-06-25T11:00:00Z",
        )

        r = client.get("/api/projects/voice-pilot/items/VP-1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "VP-1"
        assert data["title"] == "My item"
        assert data["priority"] == "high"
        assert data["type"] == "task"
        assert data["status"] == "backlog"
        assert len(data["comments"]) == 1
        assert data["comments"][0]["body"] == "First comment"

    def test_404_for_unknown_item(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        r = client.get("/api/projects/voice-pilot/items/VP-999")
        assert r.status_code == 404

    def test_404_for_unknown_project(self, client):
        r = client.get("/api/projects/ghost/items/VP-1")
        assert r.status_code == 404

    def test_empty_comments_when_none(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="No comments",
            type="task",
            now="2026-06-25T10:00:00Z",
        )
        r = client.get("/api/projects/voice-pilot/items/VP-1")
        assert r.status_code == 200
        assert r.json()["comments"] == []


class TestPatchItem:
    def test_updates_status(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="My item",
            type="task",
            now="2026-06-25T10:00:00Z",
        )
        r = client.patch(
            "/api/projects/voice-pilot/items/VP-1",
            json={"status": "in_progress"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "in_progress"
        # canonical file on disk updated
        reloaded = item_service.read_item(workspace, "VP-1")
        assert reloaded.status == "in_progress"

    def test_422_for_invalid_status(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="My item",
            type="task",
            now="2026-06-25T10:00:00Z",
        )
        r = client.patch(
            "/api/projects/voice-pilot/items/VP-1",
            json={"status": "flying"},
        )
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_404_for_unknown_project(self, client):
        r = client.patch(
            "/api/projects/ghost/items/VP-1",
            json={"status": "done"},
        )
        assert r.status_code == 404

    def test_404_for_unknown_item(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        r = client.patch(
            "/api/projects/voice-pilot/items/VP-999",
            json={"status": "done"},
        )
        assert r.status_code == 404

    def test_empty_body_succeeds(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="My item",
            type="task",
            now="2026-06-25T10:00:00Z",
        )
        r = client.patch(
            "/api/projects/voice-pilot/items/VP-1",
            json={},
        )
        assert r.status_code == 200

    def test_updates_multiple_fields(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="Original",
            type="task",
            now="2026-06-25T10:00:00Z",
        )
        r = client.patch(
            "/api/projects/voice-pilot/items/VP-1",
            json={"title": "Updated", "priority": "high"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "Updated"
        assert data["priority"] == "high"


class TestDeterministicJson:
    def test_repeated_get_identical(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="Stable",
            type="task",
            now="2026-06-25T10:00:00Z",
        )
        r1 = client.get("/api/projects/voice-pilot/items/VP-1")
        r2 = client.get("/api/projects/voice-pilot/items/VP-1")
        assert r1.json() == r2.json()

    def test_field_order_is_stable(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="Stable",
            type="task",
            now="2026-06-25T10:00:00Z",
        )
        r = client.get("/api/projects/voice-pilot/items/VP-1")
        keys = list(r.json().keys())
        # schema_version should come first (matching model field order)
        assert keys[0] == "schema_version"
        assert keys[1] == "id"
