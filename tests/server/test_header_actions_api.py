"""API tests for project unregister and doctor routes (spec 0010 R2.4, R3.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from taskpilot.core.item_io import write_item
from taskpilot.core.layout import WorkspacePaths
from taskpilot.core.models import Item, ItemLinks, ItemStatus, ItemType, Priority
from taskpilot.server.app import create_app
from taskpilot.services import item_service, project_service, registry, ui_state

NOW = "2026-06-25T10:00:00Z"


@pytest.fixture
def registry_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    d = tmp_path / "registry"
    d.mkdir()
    monkeypatch.setenv("TASKPILOT_HOME", str(d))
    return d


@pytest.fixture
def client(registry_dir: Path) -> TestClient:
    return TestClient(create_app(registry_dir=str(registry_dir)))


@pytest.fixture
def workspace(tmp_path: Path, registry_dir: Path) -> WorkspacePaths:
    paths = WorkspacePaths.for_root(tmp_path / "repo")
    project_service.create_project(paths, key="VP", name="VoicePilot", now=NOW)
    registry.register_project(
        registry_dir,
        id="voice-pilot",
        key="VP",
        name="VoicePilot",
        path=str(paths.root),
        now=NOW,
    )
    return paths


def _dangling(paths: WorkspacePaths) -> None:
    write_item(
        paths,
        Item(
            schema_version=1,
            id="VP-1",
            title="Dangling",
            type=ItemType.task,
            status=ItemStatus.backlog,
            priority=Priority.normal,
            created_at=NOW,
            updated_at=NOW,
            links=ItemLinks(blocks=["VP-99"], relates_to=[]),
        ),
    )


class TestUnregister:
    def test_delete_returns_removed_summary_and_lists_without_it(
        self, client, workspace
    ):
        r = client.delete("/api/projects/voice-pilot")
        assert r.status_code == 200
        assert r.json() == {
            "id": "voice-pilot",
            "key": "VP",
            "name": "VoicePilot",
            "active": True,
        }
        assert client.get("/api/projects").json() == []
        assert (workspace.workspace_dir / "project.yaml").is_file()

    def test_delete_unknown_returns_404(self, client, workspace):
        r = client.delete("/api/projects/nope")
        assert r.status_code == 404
        assert "Project not found" in r.json()["detail"]
        assert len(client.get("/api/projects").json()) == 1

    def test_delete_resets_last_opened(self, client, workspace):
        client.patch("/api/ui-state", json={"last_opened_project_id": "voice-pilot"})
        client.delete("/api/projects/voice-pilot")
        assert client.get("/api/ui-state").json() == {"last_opened_project_id": None}
        assert ui_state.load_ui_state().last_opened_project_id is None


class TestDoctor:
    def test_get_plan_lists_fixes_without_writing(self, client, workspace):
        _dangling(workspace)
        before = workspace.item_file("VP-1").read_bytes()

        r = client.get("/api/projects/voice-pilot/doctor")

        assert r.status_code == 200
        body = r.json()
        assert body["manual"] == []
        assert body["fixes"] == [
            {
                "kind": "remove_link",
                "item_id": "VP-1",
                "path": ".taskpilot/items/VP-1.yaml",
                "field": "links.blocks",
                "target": "VP-99",
                "description": "Remove links.blocks -> VP-99 from VP-1",
            }
        ]
        assert workspace.item_file("VP-1").read_bytes() == before

    def test_apply_repairs_and_returns_report(self, client, workspace):
        _dangling(workspace)

        r = client.post("/api/projects/voice-pilot/doctor/apply")

        assert r.status_code == 200
        body = r.json()
        assert [f["kind"] for f in body["applied"]] == ["remove_link"]
        assert body["failed"] == []
        assert body["report"]["ok"] is True
        item = item_service.read_item(workspace, "VP-1")
        assert item.links is None or item.links.blocks == []
        again = client.post("/api/projects/voice-pilot/doctor/apply").json()
        assert again["applied"] == []

    def test_unknown_project_returns_404(self, client, workspace):
        for r in (
            client.get("/api/projects/nope/doctor"),
            client.post("/api/projects/nope/doctor/apply"),
        ):
            assert r.status_code == 404
            assert "Project not found" in r.json()["detail"]

    def test_apply_conflict_is_reported_as_failed_and_leaves_files(
        self, client, workspace
    ):
        import json as _json
        import os as _os

        item_service.create_item(
            workspace, title="Done", type="task", status="done", now=NOW
        )
        root = workspace.workspace_dir / "archived"
        month = root / "2026-06"
        month.mkdir(parents=True)
        _os.replace(workspace.item_file("VP-1"), root / "VP-1.yaml")
        (month / "VP-1.yaml").write_text("different bytes\n", encoding="utf-8")
        (root / "metadata.json").write_text(
            _json.dumps(
                {
                    "VP-1": {
                        "original_id": "VP-1",
                        "project_key": "VP",
                        "archived_at": "2026-06-15T10:00:00Z",
                        "original_status": "done",
                    }
                }
            ),
            encoding="utf-8",
        )
        before = [(root / "VP-1.yaml").read_bytes(), (month / "VP-1.yaml").read_bytes()]

        r = client.post("/api/projects/voice-pilot/doctor/apply")

        assert r.status_code == 200
        body = r.json()
        assert body["applied"] == []
        assert [f["fix"]["kind"] for f in body["failed"]] == ["migrate_archive_storage"]
        assert body["failed"][0]["error"]
        assert [
            (root / "VP-1.yaml").read_bytes(),
            (month / "VP-1.yaml").read_bytes(),
        ] == before

    def test_manual_findings_include_invalid_yaml(self, client, workspace):
        (workspace.items_dir / "VP-5.yaml").write_text("id: [x\n", encoding="utf-8")
        body = client.get("/api/projects/voice-pilot/doctor").json()
        assert body["fixes"] == []
        assert [f["code"] for f in body["manual"]] == ["invalid_yaml"]


class TestDoctorSchemaParity:
    """M1: REST models mirror the domain models field for field."""

    def test_fix_plan_and_result_fields_match_domain(self):
        from taskpilot.server import schemas
        from taskpilot.services import doctor_service

        pairs = [
            (schemas.DoctorFixOut, doctor_service.DoctorFix),
            (schemas.DoctorFailureOut, doctor_service.DoctorFailure),
            (schemas.DoctorPlanOut, doctor_service.DoctorPlan),
            (schemas.DoctorResultOut, doctor_service.DoctorResult),
        ]
        for out, domain in pairs:
            assert list(out.model_fields) == list(domain.model_fields), out.__name__
        assert (
            schemas.DoctorFixOut.model_fields["kind"].annotation
            == doctor_service.DoctorFix.model_fields["kind"].annotation
        )

    def test_unknown_fix_kind_is_rejected_by_response_model(self):
        import pydantic
        from taskpilot.server import schemas

        with pytest.raises(pydantic.ValidationError):
            schemas.DoctorFixOut(
                kind="delete_everything",
                item_id=None,
                path="x",
                field=None,
                target=None,
                description="x",
            )
