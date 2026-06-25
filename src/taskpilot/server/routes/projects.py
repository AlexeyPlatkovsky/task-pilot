from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from taskpilot.services.registry import RegistryEntry, list_projects as registry_list
from taskpilot.core.layout import WorkspacePaths
from taskpilot.server.schemas import (
    ItemDetail,
    ItemSummary,
    ItemUpdateInput,
    ProjectSummary,
    ValidationFindingOut,
)
from taskpilot.services import comment_service as comment_svc
from taskpilot.services import item_service as item_svc
from taskpilot.services.errors import ValidationFailed

router = APIRouter(tags=["projects"])


def _registry_entry(request: Request, project_id: str) -> RegistryEntry:
    registry_dir: str = request.app.state.registry_dir
    for entry in registry_list(Path(registry_dir)):
        if entry.id == project_id:
            return entry
    raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")


def _paths(entry: RegistryEntry) -> WorkspacePaths:
    return WorkspacePaths.for_root(Path(entry.path))


def _item_summary(item) -> dict:
    d = item.model_dump()
    d["valid"] = True
    return d


def _item_detail(item, ws: WorkspacePaths) -> dict:
    d = item.model_dump()
    try:
        comments = comment_svc.list_comments(ws, item.id)
        d["comments"] = [c.model_dump() for c in comments]
    except ValidationFailed:
        d["comments"] = []
    d["valid"] = True
    return d


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/projects", response_model=list[ProjectSummary])
def list_all_projects(request: Request) -> list[ProjectSummary]:
    registry_dir: str = request.app.state.registry_dir
    entries = registry_list(Path(registry_dir))
    return [
        ProjectSummary(
            id=e.id,
            key=e.key,
            name=e.name,
            active=e.active,
        )
        for e in entries
    ]


@router.get(
    "/projects/{project_id}/items",
    response_model=list[ItemSummary],
)
def list_project_items(request: Request, project_id: str) -> list[ItemSummary]:
    entry = _registry_entry(request, project_id)
    ws = _paths(entry)
    items = item_svc.list_items(ws, project=entry.key, include_deleted=False)
    valid_summaries: list[ItemSummary] = [ItemSummary(**_item_summary(i)) for i in items]

    invalid_stubs = item_svc.list_invalid_item_stubs(ws, project=entry.key)
    invalid_summaries: list[ItemSummary] = [
        ItemSummary(
            id=item_id,
            title=f"[unparseable: {item_id}.yaml]",
            type="unknown",
            status="unknown",
            priority="unknown",
            valid=False,
            findings=[
                ValidationFindingOut(
                    severity="error",
                    code="parse_error",
                    path=rel_path,
                    message=error_msg,
                )
            ],
        )
        for item_id, rel_path, error_msg in invalid_stubs
    ]

    return valid_summaries + invalid_summaries


@router.get(
    "/projects/{project_id}/items/{item_id}",
    response_model=ItemDetail,
)
def get_item_detail(request: Request, project_id: str, item_id: str) -> ItemDetail:
    entry = _registry_entry(request, project_id)
    ws = _paths(entry)
    item = item_svc.read_item(ws, item_id)
    return ItemDetail(**_item_detail(item, ws))


@router.patch(
    "/projects/{project_id}/items/{item_id}",
    response_model=ItemDetail,
)
def patch_item(
    request: Request,
    project_id: str,
    item_id: str,
    body: ItemUpdateInput,
) -> ItemDetail:
    entry = _registry_entry(request, project_id)
    ws = _paths(entry)
    fields = body.model_dump(exclude_unset=True)
    item = item_svc.update_item(ws, item_id, **fields)
    return ItemDetail(**_item_detail(item, ws))
