"""API contract tests: request/response shapes, error codes, idempotency."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from taskpilot.server.app import create_app
from taskpilot.services import project_service, registry
from taskpilot.core.layout import WorkspacePaths


def _make_project(tmp_path: Path):
    """Create a project workspace with registry entry."""
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir(exist_ok=True)
    # Create workspace with project (creates .taskpilot/ automatically)
    paths = WorkspacePaths.for_root(tmp_path)
    try:
        project_service.create_project(
            paths, key="TP", name="TestProject", now="2026-08-01T00:00:00Z"
        )
    except Exception:
        pass  # Project already exists (e.g., from another fixture)
    # Register the project
    registry.register_project(
        registry_dir,
        id="TP",
        key="TP",
        name="TestProject",
        path=str(tmp_path),
        now="2026-08-01T00:00:00Z",
    )
    return registry_dir, paths


@pytest.fixture
def app(tmp_path: Path):
    registry_dir, _ = _make_project(tmp_path)
    return create_app(registry_dir=str(registry_dir))


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def workspace(tmp_path: Path):
    _, paths = _make_project(tmp_path)
    return paths


class TestArchiveRunContract:
    def test_response_shape(self, client):
        resp = client.post("/api/projects/TP/archive/run")
        assert resp.status_code == 200
        data = resp.json()
        assert "archived" in data
        assert isinstance(data["archived"], list)

    def test_idempotent(self, client):
        resp1 = client.post("/api/projects/TP/archive/run")
        resp2 = client.post("/api/projects/TP/archive/run")
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["archived"] == resp2.json()["archived"] == []


class TestArchiveMigrateContract:
    def test_response_shape(self, client):
        resp = client.post("/api/projects/TP/archive/migrate")
        assert resp.status_code == 200
        data = resp.json()
        assert "archived_count" in data
        assert "archived_ids" in data
        assert isinstance(data["archived_count"], int)
        assert isinstance(data["archived_ids"], list)


class TestArchiveStorageMigrateContract:
    def test_response_shape(self, client, workspace):
        from taskpilot.core.item_io import write_item
        from taskpilot.core.models import Item, ItemStatus, ItemType, Priority

        item = Item(
            schema_version=1,
            id="TP-1",
            title="Legacy archived item",
            type=ItemType.task,
            status=ItemStatus.done,
            priority=Priority.normal,
            created_at="2026-05-01T00:00:00Z",
            updated_at="2026-05-01T00:00:00Z",
        )
        write_item(workspace, item)
        second_item = Item(
            **(
                item.model_dump(mode="json")
                | {"id": "TP-2", "title": "Second legacy item"}
            )
        )
        write_item(workspace, second_item)
        root = workspace.workspace_dir / "archived"
        root.mkdir()
        workspace.item_file("TP-1").replace(root / "TP-1.yaml")
        workspace.item_file("TP-2").replace(root / "TP-2.yaml")
        (root / "metadata.json").write_text(
            '{"TP-2":{"original_id":"TP-2","project_key":"TP",'
            '"archived_at":"2026-07-15T10:00:00Z","original_status":"done"},'
            '"TP-1":{"original_id":"TP-1","project_key":"TP",'
            '"archived_at":"2026-06-15T10:00:00Z","original_status":"done"}}',
            encoding="utf-8",
        )
        resp = client.post("/api/projects/TP/archive/migrate-storage")

        assert resp.status_code == 200
        assert resp.json() == {
            "migrated_count": 2,
            "migrated_ids": ["TP-1", "TP-2"],
        }
        assert (root / "2026-06" / "TP-1.yaml").is_file()
        assert (root / "2026-07" / "TP-2.yaml").is_file()


class TestUnarchiveContract:
    def test_response_shape(self, client, workspace):
        # Create and archive an item
        from taskpilot.core.models import Item, ItemStatus, ItemType, Priority
        from taskpilot.core.item_io import write_item

        item = Item(
            schema_version=1,
            id="TP-1",
            title="Test Item",
            type=ItemType.task,
            status=ItemStatus.done,
            priority=Priority.normal,
            created_at="2026-07-10T00:00:00Z",
            updated_at="2026-07-20T00:00:00Z",
        )
        write_item(workspace, item)
        # Archive it
        client.post("/api/projects/TP/archive/run")
        resp = client.post("/api/projects/TP/items/TP-1/unarchive")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["id"] == "TP-1"

    def test_404_for_unknown_project(self, client):
        resp = client.post("/api/projects/UNKNOWN/archive/run")
        assert resp.status_code == 404

    def test_404_for_non_archived_item(self, client):
        resp = client.post("/api/projects/TP/items/TP-999/unarchive")
        assert resp.status_code == 404

    def test_409_for_occupied_unarchive_destination_without_overwrite(
        self, client, workspace
    ):
        from taskpilot.core.item_io import write_item
        from taskpilot.core.models import Item, ItemStatus, ItemType, Priority

        archived_item = Item(
            schema_version=1,
            id="TP-1",
            title="Archived item",
            type=ItemType.task,
            status=ItemStatus.done,
            priority=Priority.normal,
            created_at="2026-07-10T00:00:00Z",
            updated_at="2026-07-20T00:00:00Z",
        )
        write_item(workspace, archived_item)
        assert client.post("/api/projects/TP/archive/run").status_code == 200
        archived_file = workspace.workspace_dir / "archived" / "2026-08" / "TP-1.yaml"
        metadata_file = (
            workspace.workspace_dir / "archived" / "2026-08" / "metadata.json"
        )
        archived_before = archived_file.read_bytes()
        metadata_before = metadata_file.read_bytes()

        active_item = Item(
            **(
                archived_item.model_dump(mode="json")
                | {"title": "Active replacement", "status": ItemStatus.backlog}
            )
        )
        write_item(workspace, active_item)
        active_before = workspace.item_file("TP-1").read_bytes()

        resp = client.post("/api/projects/TP/items/TP-1/unarchive")

        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]
        assert workspace.item_file("TP-1").read_bytes() == active_before
        assert archived_file.read_bytes() == archived_before
        assert metadata_file.read_bytes() == metadata_before


class TestSettingsContract:
    def test_get_response_shape(self, client):
        resp = client.get("/api/projects/TP/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert "archive_threshold_days" in data
        assert isinstance(data["archive_threshold_days"], int)

    def test_patch_response_shape(self, client):
        resp = client.patch(
            "/api/projects/TP/settings", json={"archive_threshold_days": 21}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["archive_threshold_days"] == 21

    def test_400_for_invalid_threshold(self, client):
        resp = client.patch(
            "/api/projects/TP/settings", json={"archive_threshold_days": 0}
        )
        assert resp.status_code == 400

    def test_400_for_above_max(self, client):
        resp = client.patch(
            "/api/projects/TP/settings", json={"archive_threshold_days": 10000}
        )
        assert resp.status_code == 400


class TestListArchivedContract:
    def test_response_shape(self, client):
        resp = client.get("/api/projects/TP/archived")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
