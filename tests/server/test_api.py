"""API integration tests for the FastAPI server (task F005-T8).

Covers all endpoints, 404 paths, 400/422 error responses, null-field clearing,
malformed-comment resilience, invalid-file surfacing, and deterministic JSON
serialization using FastAPI TestClient.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from taskpilot.services.registry import (
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

    app = create_app(registry_dir=str(registry_dir))
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

    def test_valid_summary_findings_is_empty_list(self, client, tmp_path, workspace):
        """Valid item summaries serialize findings as [] (not null) for a stable contract (F-3)."""
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace, title="Good item", type="task", now="2026-06-25T10:00:00Z"
        )
        r = client.get("/api/projects/voice-pilot/items")
        assert r.status_code == 200
        summary = r.json()[0]
        assert summary["valid"] is True
        assert summary["findings"] == []

    def test_summary_includes_dates_for_list_view(self, client, tmp_path, workspace):
        """F006 list view needs stable date fields without fetching item details."""
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace, title="Dated item", type="task", now="2026-06-25T10:00:00Z"
        )

        r = client.get("/api/projects/voice-pilot/items")

        assert r.status_code == 200
        summary = r.json()[0]
        assert summary["created_at"] == "2026-06-25T10:00:00Z"
        assert summary["updated_at"] == "2026-06-25T10:00:00Z"

    def test_summary_includes_parent_id_for_tree_view(
        self, client, tmp_path, workspace
    ):
        """F006 tree view derives hierarchy from the already-loaded item list."""
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace, title="Epic", type="epic", now="2026-06-25T10:00:00Z"
        )
        item_service.create_item(
            workspace,
            title="Feature",
            type="feature",
            parent_id="VP-1",
            now="2026-06-25T10:01:00Z",
        )

        r = client.get("/api/projects/voice-pilot/items")

        assert r.status_code == 200
        child = next(item for item in r.json() if item["id"] == "VP-2")
        assert child["parent_id"] == "VP-1"

    def test_invalid_item_file_surfaces_as_invalid_summary(
        self, client, tmp_path, workspace
    ):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace, title="Good item", type="task", now="2026-06-25T10:00:00Z"
        )
        # Write a corrupt item file
        bad_file = workspace.items_dir / "VP-99.yaml"
        bad_file.write_text("not: valid: yaml: [\n", encoding="utf-8")

        r = client.get("/api/projects/voice-pilot/items")
        assert r.status_code == 200
        data = r.json()
        ids = [item["id"] for item in data]
        assert "VP-1" in ids
        assert "VP-99" in ids
        invalid = next(item for item in data if item["id"] == "VP-99")
        assert invalid["valid"] is False
        assert invalid["findings"] is not None
        assert len(invalid["findings"]) == 1
        assert invalid["findings"][0]["code"] == "parse_error"


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

    def test_valid_detail_findings_is_empty_list(self, client, tmp_path, workspace):
        """Valid item details serialize findings as [] (not null) for a stable contract (F-3)."""
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace, title="My item", type="task", now="2026-06-25T10:00:00Z"
        )
        r = client.get("/api/projects/voice-pilot/items/VP-1")
        assert r.status_code == 200
        assert r.json()["findings"] == []

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

    def test_malformed_comment_does_not_block_item(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="Item with bad comment",
            type="task",
            now="2026-06-25T10:00:00Z",
        )
        comment_dir = workspace.item_comments_dir("VP-1")
        comment_dir.mkdir(parents=True, exist_ok=True)
        (comment_dir / "2026-06-25T10-00-01Z.md").write_text(
            "not frontmatter at all", encoding="utf-8"
        )

        r = client.get("/api/projects/voice-pilot/items/VP-1")
        assert r.status_code == 200
        assert r.json()["comments"] == []

    def test_malformed_comment_does_not_block_patch(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="Item with bad comment",
            type="task",
            now="2026-06-25T10:00:00Z",
        )
        comment_dir = workspace.item_comments_dir("VP-1")
        comment_dir.mkdir(parents=True, exist_ok=True)
        (comment_dir / "2026-06-25T10-00-01Z.md").write_text(
            "not frontmatter at all", encoding="utf-8"
        )

        r = client.patch(
            "/api/projects/voice-pilot/items/VP-1",
            json={"status": "done"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "done"


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
        reloaded = item_service.read_item(workspace, "VP-1")
        assert reloaded.status == "in_progress"

    def test_400_for_invalid_status(self, client, tmp_path, workspace):
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
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_422_for_malformed_body(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace, title="My item", type="task", now="2026-06-25T10:00:00Z"
        )
        r = client.patch(
            "/api/projects/voice-pilot/items/VP-1",
            json={"status": 12345},
        )
        assert r.status_code == 422

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

    def test_empty_body_is_noop_and_keeps_updated_at(self, client, tmp_path, workspace):
        """An empty PATCH returns the item unchanged without bumping updated_at (F-5)."""
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
        assert r.json()["updated_at"] == "2026-06-25T10:00:00Z"
        reloaded = item_service.read_item(workspace, "VP-1")
        assert reloaded.updated_at == "2026-06-25T10:00:00Z"

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

    def test_null_clears_optional_field(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="Item with description",
            type="task",
            description="initial description",
            now="2026-06-25T10:00:00Z",
        )
        r = client.get("/api/projects/voice-pilot/items/VP-1")
        assert r.json()["description"] == "initial description"

        r = client.patch(
            "/api/projects/voice-pilot/items/VP-1",
            json={"description": None},
        )
        assert r.status_code == 200
        assert r.json()["description"] is None

        reloaded = item_service.read_item(workspace, "VP-1")
        assert reloaded.description is None


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
        assert keys[0] == "schema_version"
        assert keys[1] == "id"


def _write_foreign_item(workspace: WorkspacePaths, item_id: str) -> None:
    """Write a syntactically valid item file whose id does not match the project key."""
    workspace.items_dir.mkdir(parents=True, exist_ok=True)
    (workspace.items_dir / f"{item_id}.yaml").write_text(
        "schema_version: 1\n"
        f"id: {item_id}\n"
        "title: Foreign item\n"
        "priority: normal\n"
        "type: task\n"
        "status: backlog\n"
        "created_at: '2026-06-25T10:00:00Z'\n"
        "updated_at: '2026-06-25T10:00:00Z'\n",
        encoding="utf-8",
    )


class TestItemScoping:
    """Item endpoints must reject ids that do not belong to the path project (F-4)."""

    def test_get_404_for_foreign_key_item(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        _write_foreign_item(workspace, "XX-1")
        r = client.get("/api/projects/voice-pilot/items/XX-1")
        assert r.status_code == 404

    def test_patch_404_for_foreign_key_item(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        _write_foreign_item(workspace, "XX-1")
        r = client.patch(
            "/api/projects/voice-pilot/items/XX-1",
            json={"status": "done"},
        )
        assert r.status_code == 404
        # The foreign file must be left untouched by the rejected write.
        assert "status: backlog" in (workspace.items_dir / "XX-1.yaml").read_text(
            encoding="utf-8"
        )


class TestAppFactory:
    """The env-based factory lets the CLI launch the server without importing it (F-2)."""

    def test_create_app_from_env_builds_working_app(self, tmp_path, monkeypatch):
        from taskpilot.server.app import create_app_from_env

        registry_dir = tmp_path / "registry"
        registry_dir.mkdir()
        monkeypatch.setenv("TASKPILOT_REGISTRY_DIR", str(registry_dir))

        app = create_app_from_env()
        c = TestClient(app)
        assert c.get("/api/health").status_code == 200

    def test_create_app_from_env_requires_env_var(self, monkeypatch):
        from taskpilot.server.app import create_app_from_env

        monkeypatch.delenv("TASKPILOT_REGISTRY_DIR", raising=False)
        with pytest.raises(RuntimeError):
            create_app_from_env()
