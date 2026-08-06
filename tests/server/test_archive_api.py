"""API integration tests for archive endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from taskpilot.server.app import create_app
from taskpilot.services import archive_service, project_service, registry
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


class TestGetProjectSettings:
    def test_returns_default_threshold(self, client):
        resp = client.get("/api/projects/TP/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["archive_threshold_days"] == 14

    def test_returns_custom_threshold(self, client):
        resp = client.patch(
            "/api/projects/TP/settings", json={"archive_threshold_days": 30}
        )
        assert resp.status_code == 200
        resp = client.get("/api/projects/TP/settings")
        assert resp.json()["archive_threshold_days"] == 30


class TestPatchProjectSettings:
    def test_rejects_invalid_threshold(self, client):
        resp = client.patch(
            "/api/projects/TP/settings", json={"archive_threshold_days": 0}
        )
        assert resp.status_code == 400

    def test_rejects_above_max(self, client):
        resp = client.patch(
            "/api/projects/TP/settings", json={"archive_threshold_days": 9999}
        )
        assert resp.status_code == 400

    def test_accepts_valid_threshold(self, client):
        resp = client.patch(
            "/api/projects/TP/settings", json={"archive_threshold_days": 7}
        )
        assert resp.status_code == 200
        assert resp.json()["archive_threshold_days"] == 7


class TestArchiveRun:
    def test_returns_empty_when_no_eligible(self, client):
        resp = client.post("/api/projects/TP/archive/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["archived"] == []

    def test_archives_eligible_items(self, client, workspace):
        # Create an eligible item
        from taskpilot.core.models import Item, ItemStatus, ItemType, Priority

        item = Item(
            schema_version=1,
            id="TP-1",
            title="Old Done Item",
            type=ItemType.task,
            status=ItemStatus.done,
            priority=Priority.normal,
            created_at="2026-07-10T00:00:00Z",
            updated_at="2026-07-20T00:00:00Z",
        )
        from taskpilot.core.item_io import write_item

        write_item(workspace, item)

        resp = client.post("/api/projects/TP/archive/run")
        assert resp.status_code == 200
        data = resp.json()
        assert "TP-1" in data["archived"]


class TestArchiveMigrate:
    def test_returns_summary(self, client, workspace):
        # Create eligible items
        from taskpilot.core.models import Item, ItemStatus, ItemType, Priority
        from taskpilot.core.item_io import write_item

        for i in (1, 2):
            item = Item(
                schema_version=1,
                id=f"TP-{i}",
                title=f"Item {i}",
                type=ItemType.task,
                status=ItemStatus.done,
                priority=Priority.normal,
                created_at="2026-07-10T00:00:00Z",
                updated_at="2026-07-20T00:00:00Z",
            )
            write_item(workspace, item)

        resp = client.post("/api/projects/TP/archive/migrate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["archived_count"] == 2
        assert sorted(data["archived_ids"]) == ["TP-1", "TP-2"]


class TestUnarchiveItem:
    def test_restores_item(self, client, workspace):
        from taskpilot.core.models import Item, ItemStatus, ItemType, Priority
        from taskpilot.core.item_io import write_item

        # Create and archive an item
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
        # Unarchive
        resp = client.post("/api/projects/TP/items/TP-1/unarchive")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "TP-1"

    def test_returns_404_for_non_archived(self, client):
        resp = client.post("/api/projects/TP/items/TP-999/unarchive")
        assert resp.status_code == 404


class TestListArchivedItems:
    def test_returns_empty_when_no_archived(self, client):
        resp = client.get("/api/projects/TP/archived")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_archived_items(self, client, workspace):
        from taskpilot.core.models import Item, ItemStatus, ItemType, Priority
        from taskpilot.core.item_io import write_item

        # Create and archive items
        for i in (1, 2):
            item = Item(
                schema_version=1,
                id=f"TP-{i}",
                title=f"Item {i}",
                type=ItemType.task,
                status=ItemStatus.done,
                priority=Priority.normal,
                created_at="2026-07-10T00:00:00Z",
                updated_at="2026-07-20T00:00:00Z",
            )
            write_item(workspace, item)
        client.post("/api/projects/TP/archive/run")
        resp = client.get("/api/projects/TP/archived")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        ids = {item["id"] for item in data}
        assert ids == {"TP-1", "TP-2"}

    def test_excludes_archived_items_from_another_project_key(self, client, workspace):
        from taskpilot.core.item_io import write_item
        from taskpilot.core.models import Item, ItemStatus, ItemType, Priority

        for item_id in ("TP-1", "XX-1"):
            write_item(
                workspace,
                Item(
                    schema_version=1,
                    id=item_id,
                    title=item_id,
                    type=ItemType.task,
                    status=ItemStatus.done,
                    priority=Priority.normal,
                    created_at="2026-06-01T00:00:00Z",
                    updated_at="2026-06-01T00:00:00Z",
                ),
            )
        assert archive_service.archive_items(
            workspace, ["TP-1", "XX-1"], now="2026-06-16T00:00:00Z"
        ) == ["TP-1", "XX-1"]

        response = client.get("/api/projects/TP/archived")

        assert response.status_code == 200
        assert [item["id"] for item in response.json()] == ["TP-1"]


class TestArchivedItemDetail:
    def test_returns_detail_for_an_archived_item(self, client, workspace):
        from taskpilot.core.item_io import write_item
        from taskpilot.core.models import Item, ItemStatus, ItemType, Priority

        item = Item(
            schema_version=1,
            id="TP-1",
            title="Archived detail item",
            type=ItemType.task,
            status=ItemStatus.done,
            priority=Priority.normal,
            created_at="2026-07-10T00:00:00Z",
            updated_at="2026-07-20T00:00:00Z",
            description="Preserved archive detail",
        )
        write_item(workspace, item)
        assert client.post("/api/projects/TP/archive/run").status_code == 200

        response = client.get("/api/projects/TP/items/TP-1")

        assert response.status_code == 200
        assert response.json()["id"] == "TP-1"
        assert response.json()["description"] == "Preserved archive detail"
        assert response.json()["archived"] is True

    def test_keeps_corrupt_archived_item_visible_and_actionable(
        self, client, workspace
    ):
        from taskpilot.core.item_io import write_item
        from taskpilot.core.models import Item, ItemStatus, ItemType, Priority

        write_item(
            workspace,
            Item(
                schema_version=1,
                id="TP-1",
                title="Will become corrupt",
                type=ItemType.task,
                status=ItemStatus.done,
                priority=Priority.normal,
                created_at="2026-07-10T00:00:00Z",
                updated_at="2026-07-20T00:00:00Z",
            ),
        )
        assert client.post("/api/projects/TP/archive/run").status_code == 200
        archived_file = next((workspace.workspace_dir / "archived").glob("*/TP-1.yaml"))
        archived_file.write_text("id: TP-1\n  invalid: yaml\n", encoding="utf-8")

        validation = client.get("/api/projects/TP/validate")
        listing = client.get("/api/projects/TP/archived")
        detail = client.get("/api/projects/TP/items/TP-1")

        assert validation.status_code == 200
        assert any(
            finding["code"] == "invalid_yaml"
            for finding in validation.json()["findings"]
        )
        assert listing.status_code == 200
        assert listing.json()[0]["id"] == "TP-1"
        assert listing.json()[0]["valid"] is False
        assert detail.status_code == 200
        assert detail.json()["id"] == "TP-1"
        assert detail.json()["valid"] is False
