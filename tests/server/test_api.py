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
from taskpilot.server.schemas import ItemRelationshipSummary, ItemSummary
from taskpilot.services import item_service, link_service, project_service


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

    def test_detail_marks_parseable_item_invalid_with_item_scoped_findings(
        self, client, tmp_path, workspace
    ):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="Item with broken link",
            type="task",
            now="2026-06-25T10:00:00Z",
        )
        workspace.item_file("VP-1").write_text(
            "schema_version: 1\n"
            "id: VP-1\n"
            "title: Item with broken link\n"
            "priority: normal\n"
            "type: task\n"
            "status: backlog\n"
            "created_at: '2026-06-25T10:00:00Z'\n"
            "updated_at: '2026-06-25T10:00:00Z'\n"
            "links:\n"
            "  blocks:\n"
            "    - VP-404\n",
            encoding="utf-8",
        )

        r = client.get("/api/projects/voice-pilot/items/VP-1")

        assert r.status_code == 200
        detail = r.json()
        assert detail["id"] == "VP-1"
        assert detail["valid"] is False
        assert detail["findings"] == [
            {
                "severity": "error",
                "code": "missing_reference",
                "path": ".taskpilot/items/VP-1.yaml",
                "field": "links.blocks",
                "item_id": "VP-1",
                "message": "links.blocks references unknown item: VP-404",
            }
        ]

    def test_detail_returns_invalid_payload_for_item_file_with_validation_errors(
        self, client, tmp_path, workspace
    ):
        _setup_registry(workspace, tmp_path)
        workspace.items_dir.mkdir(parents=True, exist_ok=True)
        workspace.item_file("VP-99").write_text(
            "schema_version: bad\n"
            "id: ''\n"
            "priority: normal\n"
            "type: task\n"
            "status: backlog\n"
            "created_at: '2026-06-25T10:00:00Z'\n"
            "updated_at: '2026-06-25T10:00:00Z'\n"
            "tags:\n"
            "  - beta\n"
            "description: Keep this parsed description visible.\n"
            "attachments:\n"
            "  - docs/example.md\n"
            "dor:\n"
            "  - Ready criterion\n"
            "dod:\n"
            "  - Done criterion\n"
            "external_refs:\n"
            "  - https://example.test/ref\n",
            encoding="utf-8",
        )

        r = client.get("/api/projects/voice-pilot/items/VP-99")

        assert r.status_code == 200
        detail = r.json()
        assert detail["schema_version"] == 1
        assert detail["id"] == "VP-99"
        assert detail["title"] == "[invalid: VP-99.yaml]"
        assert detail["tags"] == ["beta"]
        assert detail["description"] == "Keep this parsed description visible."
        assert detail["attachments"] == ["docs/example.md"]
        assert detail["dor"] == ["Ready criterion"]
        assert detail["dod"] == ["Done criterion"]
        assert detail["external_refs"] == ["https://example.test/ref"]
        assert detail["valid"] is False
        assert {
            (finding["code"], finding["field"], finding["message"])
            for finding in detail["findings"]
        } == {
            (
                "invalid_field",
                "schema_version",
                "schema_version: Input should be a valid integer, unable to parse string as an integer",
            ),
            (
                "invalid_field",
                "id",
                "id: String should have at least 1 character",
            ),
            ("missing_required_field", "title", "Missing required field: title"),
        }

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

    def test_detail_includes_derived_relationships(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        item_service.create_item(
            workspace,
            title="Parent epic",
            type="epic",
            now="2026-06-25T10:00:00Z",
        )
        item_service.create_item(
            workspace,
            title="Target feature",
            type="feature",
            parent_id="VP-1",
            now="2026-06-25T10:01:00Z",
        )
        item_service.create_item(
            workspace,
            title="Child task",
            type="task",
            parent_id="VP-2",
            now="2026-06-25T10:02:00Z",
        )
        item_service.create_item(
            workspace,
            title="Blocked target",
            type="task",
            now="2026-06-25T10:03:00Z",
        )
        item_service.create_item(
            workspace,
            title="Related target",
            type="task",
            now="2026-06-25T10:04:00Z",
        )
        item_service.create_item(
            workspace,
            title="Incoming blocker",
            type="task",
            now="2026-06-25T10:05:00Z",
        )
        item_service.create_item(
            workspace,
            title="Incoming related",
            type="task",
            now="2026-06-25T10:06:00Z",
        )
        link_service.add_link(workspace, "VP-2", "blocks", "VP-4")
        link_service.add_link(workspace, "VP-2", "relates_to", "VP-5")
        link_service.add_link(workspace, "VP-6", "blocks", "VP-2")
        link_service.add_link(workspace, "VP-7", "relates_to", "VP-2")

        r = client.get("/api/projects/voice-pilot/items/VP-2")

        assert r.status_code == 200
        relationships = r.json()["relationships"]
        assert relationships["parent"] == {
            "id": "VP-1",
            "title": "Parent epic",
            "type": "epic",
            "status": "backlog",
            "priority": "normal",
            "valid": True,
        }
        assert relationships["children"] == [
            {
                "id": "VP-3",
                "title": "Child task",
                "type": "task",
                "status": "backlog",
                "priority": "normal",
                "valid": True,
            }
        ]
        assert relationships["blocks"][0]["id"] == "VP-4"
        assert relationships["relates_to"][0]["id"] == "VP-5"
        assert relationships["blocked_by"][0]["id"] == "VP-6"
        assert relationships["related_to"][0]["id"] == "VP-7"

    def test_detail_keeps_missing_relationship_ids_visible(
        self, client, tmp_path, workspace
    ):
        _setup_registry(workspace, tmp_path)
        workspace.items_dir.mkdir(parents=True, exist_ok=True)
        workspace.item_file("VP-1").write_text(
            "schema_version: 1\n"
            "id: VP-1\n"
            "title: Item with broken relationships\n"
            "priority: normal\n"
            "type: feature\n"
            "status: backlog\n"
            "created_at: '2026-06-25T10:00:00Z'\n"
            "updated_at: '2026-06-25T10:00:00Z'\n"
            "parent_id: VP-404\n"
            "links:\n"
            "  blocks:\n"
            "    - VP-405\n",
            encoding="utf-8",
        )

        r = client.get("/api/projects/voice-pilot/items/VP-1")

        assert r.status_code == 200
        relationships = r.json()["relationships"]
        assert relationships["parent"] == {
            "id": "VP-404",
            "title": "[missing item]",
            "type": "unknown",
            "status": "unknown",
            "priority": "unknown",
            "valid": False,
        }
        assert relationships["blocks"] == [
            {
                "id": "VP-405",
                "title": "[missing item]",
                "type": "unknown",
                "status": "unknown",
                "priority": "unknown",
                "valid": False,
            }
        ]

    def test_relationship_summary_schema_tracks_item_summary_overlap(self):
        item_fields = ItemSummary.model_fields
        relationship_fields = ItemRelationshipSummary.model_fields
        relationship_field_names = set(relationship_fields)

        assert relationship_field_names == {
            "id",
            "title",
            "type",
            "status",
            "priority",
            "valid",
        }
        assert relationship_field_names <= set(item_fields)
        for field_name in relationship_field_names:
            item_field = item_fields[field_name]
            relationship_field = relationship_fields[field_name]
            assert relationship_field.annotation == item_field.annotation
            assert relationship_field.default == item_field.default
            assert relationship_field.alias == item_field.alias


class TestValidateProject:
    def test_returns_validation_report(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        bad_file = workspace.items_dir / "VP-3.yaml"
        bad_file.write_text(
            "schema_version: 1\n"
            "id: VP-3\n"
            "priority: normal\n"
            "type: task\n"
            "status: backlog\n"
            "created_at: '2026-06-25T10:00:00Z'\n"
            "updated_at: '2026-06-25T10:00:00Z'\n",
            encoding="utf-8",
        )

        r = client.get("/api/projects/voice-pilot/validate")

        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is False
        assert data["summary"] == {"errors": 1, "warnings": 0}
        assert data["findings"][0]["path"] == ".taskpilot/items/VP-3.yaml"
        assert data["findings"][0]["item_id"] == "VP-3"
        assert data["findings"][0]["message"] == "Missing required field: title"

    def test_404_for_unknown_project(self, client):
        r = client.get("/api/projects/ghost/validate")
        assert r.status_code == 404
        assert r.json() == {"detail": "Project not found: ghost"}


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


class TestUIState:
    """F010-T6/F010-T12: GET /api/ui-state and PATCH /api/ui-state."""

    def test_get_returns_default_when_no_file(self, client):
        r = client.get("/api/ui-state")
        assert r.status_code == 200
        assert r.json() == {"last_opened_project_id": None}

    def test_patch_saves_and_returns_last_opened_project_id(
        self, client, tmp_path, workspace
    ):
        _setup_registry(workspace, tmp_path)
        r = client.patch(
            "/api/ui-state",
            json={"last_opened_project_id": "voice-pilot"},
        )
        assert r.status_code == 200
        assert r.json() == {"last_opened_project_id": "voice-pilot"}

        r2 = client.get("/api/ui-state")
        assert r2.json() == {"last_opened_project_id": "voice-pilot"}

    def test_patch_null_clears_last_opened_project_id(
        self, client, tmp_path, workspace
    ):
        _setup_registry(workspace, tmp_path)
        client.patch(
            "/api/ui-state",
            json={"last_opened_project_id": "voice-pilot"},
        )
        r = client.patch(
            "/api/ui-state",
            json={"last_opened_project_id": None},
        )
        assert r.status_code == 200
        assert r.json() == {"last_opened_project_id": None}

    def test_patch_empty_body_preserves_last_opened_project_id(
        self, client, tmp_path, workspace
    ):
        _setup_registry(workspace, tmp_path)
        client.patch(
            "/api/ui-state",
            json={"last_opened_project_id": "voice-pilot"},
        )

        r = client.patch("/api/ui-state", json={})

        assert r.status_code == 200
        assert r.json() == {"last_opened_project_id": "voice-pilot"}

    def test_patch_rejects_unknown_fields(self, client):
        r = client.patch(
            "/api/ui-state",
            json={"last_opened_project_id": "voice-pilot", "foo": "bar"},
        )
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_patch_rejects_unknown_project_id(self, client):
        r = client.patch(
            "/api/ui-state",
            json={"last_opened_project_id": "ghost"},
        )
        assert r.status_code == 400
        assert "Unknown or inactive project" in r.json()["detail"]

    def test_patch_rejects_inactive_project(self, client, tmp_path, workspace):
        _setup_registry(workspace, tmp_path)
        registry_dir = tmp_path / "registry"
        from taskpilot.services.registry import load_registry, save_registry

        reg = load_registry(registry_dir)
        reg.projects[0].active = False
        save_registry(registry_dir, reg)

        r = client.patch(
            "/api/ui-state",
            json={"last_opened_project_id": "voice-pilot"},
        )
        assert r.status_code == 400
        assert "Unknown or inactive project" in r.json()["detail"]


class TestWebUIServing:
    """F009-T8: WebUI static serving with TASKPILOT_WEB_DIST."""

    @pytest.fixture
    def webui_app(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        from taskpilot.server.app import create_app

        registry_dir = tmp_path / "registry"
        registry_dir.mkdir()
        monkeypatch.setenv("TASKPILOT_HOME", str(registry_dir))
        return create_app(registry_dir=str(registry_dir))

    @pytest.fixture
    def webui_dist(self, tmp_path: Path) -> Path:
        dist = tmp_path / "web-dist"
        dist.mkdir()
        (dist / "index.html").write_text(
            "<!DOCTYPE html><html><head><title>TaskPilot</title></head><body>App</body></html>",
            encoding="utf-8",
        )
        assets = dist / "assets"
        assets.mkdir()
        (assets / "main.js").write_text("console.log('test');", encoding="utf-8")
        (dist / "favicon.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><title>Favicon</title></svg>',
            encoding="utf-8",
        )
        (dist / "task-pilot-compass-board.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><title>Logo</title></svg>',
            encoding="utf-8",
        )
        return dist

    def test_no_web_dist_env_serves_only_api(self, webui_app):
        """When TASKPILOT_WEB_DIST is unset, only API routes are available."""
        c = TestClient(webui_app)
        assert c.get("/api/health").status_code == 200
        # Root returns 404 (fallback route not registered)
        assert c.get("/").status_code == 404

    def test_valid_web_dist_serves_spa_fallback(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ):
        """With a valid web-dist, index.html is served and API still works."""
        dist = tmp_path / "web-dist"
        dist.mkdir()
        (dist / "index.html").write_text(
            "<!DOCTYPE html><html><head><title>TaskPilot</title></head><body>App</body></html>",
            encoding="utf-8",
        )
        assets = dist / "assets"
        assets.mkdir()
        (assets / "main.js").write_text("console.log('test');", encoding="utf-8")
        (dist / "favicon.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><title>Favicon</title></svg>',
            encoding="utf-8",
        )
        (dist / "task-pilot-compass-board.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><title>Logo</title></svg>',
            encoding="utf-8",
        )

        monkeypatch.setenv("TASKPILOT_WEB_DIST", str(dist))
        from taskpilot.server.app import create_app

        registry_dir = tmp_path / "registry"
        registry_dir.mkdir()
        monkeypatch.setenv("TASKPILOT_HOME", str(registry_dir))
        app = create_app(registry_dir=str(registry_dir))
        c = TestClient(app)

        assert c.get("/api/health").status_code == 200
        r = c.get("/")
        assert r.status_code == 200
        assert "<title>TaskPilot</title>" in r.text
        r = c.get("/projects/foo")
        assert r.status_code == 200
        assert "<title>TaskPilot</title>" in r.text
        r = c.get("/assets/main.js")
        assert r.status_code == 200
        assert r.text == "console.log('test');"
        r = c.get("/favicon.svg")
        assert r.status_code == 200
        assert "image/svg+xml" in r.headers["content-type"]
        assert "<title>Favicon</title>" in r.text
        r = c.get("/task-pilot-compass-board.svg")
        assert r.status_code == 200
        assert "image/svg+xml" in r.headers["content-type"]
        assert "<title>Logo</title>" in r.text

    def test_valid_web_dist_does_not_spa_fallback_unknown_api(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ):
        """Unknown API routes must stay API 404s rather than serving index.html."""
        dist = tmp_path / "web-dist"
        dist.mkdir()
        (dist / "index.html").write_text(
            "<!DOCTYPE html><html><head><title>TaskPilot</title></head><body>App</body></html>",
            encoding="utf-8",
        )
        assets = dist / "assets"
        assets.mkdir()
        (assets / "main.js").write_text("console.log('test');", encoding="utf-8")

        monkeypatch.setenv("TASKPILOT_WEB_DIST", str(dist))
        from taskpilot.server.app import create_app

        registry_dir = tmp_path / "registry"
        registry_dir.mkdir()
        monkeypatch.setenv("TASKPILOT_HOME", str(registry_dir))
        app = create_app(registry_dir=str(registry_dir))
        c = TestClient(app)

        r = c.get("/api/nope")
        assert r.status_code == 404
        assert r.headers["content-type"] == "application/json"
        assert r.json() == {"detail": "Not Found"}

    def test_web_dist_missing_assets_returns_packaging_error(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ):
        """An incomplete WebUI build reports the packaging error instead of crashing."""
        dist = tmp_path / "web-dist"
        dist.mkdir()
        (dist / "index.html").write_text(
            "<!DOCTYPE html><html><head><title>TaskPilot</title></head><body>App</body></html>",
            encoding="utf-8",
        )

        monkeypatch.setenv("TASKPILOT_WEB_DIST", str(dist))
        from taskpilot.server.app import create_app

        registry_dir = tmp_path / "registry"
        registry_dir.mkdir()
        monkeypatch.setenv("TASKPILOT_HOME", str(registry_dir))
        app = create_app(registry_dir=str(registry_dir))
        c = TestClient(app)

        assert c.get("/api/health").status_code == 200
        r = c.get("/")
        assert r.status_code == 503
        assert "WebUI assets are not available" in r.text

    def test_missing_web_dist_returns_packaging_error(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ):
        """When TASKPILOT_WEB_DIST points to a missing directory, 503 is returned."""
        missing = str(tmp_path / "nonexistent")
        monkeypatch.setenv("TASKPILOT_WEB_DIST", missing)
        from taskpilot.server.app import create_app

        registry_dir = tmp_path / "registry"
        registry_dir.mkdir()
        monkeypatch.setenv("TASKPILOT_HOME", str(registry_dir))
        app = create_app(registry_dir=str(registry_dir))
        c = TestClient(app)

        assert c.get("/api/health").status_code == 200
        r = c.get("/")
        assert r.status_code == 503
        assert "WebUI assets are not available" in r.text
        r = c.get("/some/page")
        assert r.status_code == 503
        assert "WebUI assets are not available" in r.text
