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
    UIStateOut,
    UIStatePatch,
    ValidationFindingOut,
    ValidationReportOut,
)
from taskpilot.core.validation import validate_workspace
from taskpilot.services import comment_service as comment_svc
from taskpilot.services import item_service as item_svc
from taskpilot.services import ui_state as ui_state_svc
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


def _require_item_in_project(entry: RegistryEntry, item_id: str) -> None:
    """Reject item ids that do not belong to the path project's key (404).

    Item ids are project-key prefixed (e.g. ``VP-1``). Scoping the lookup to the
    path ``project_id`` keeps the route honest if a workspace ever holds items
    from more than one project key.
    """
    if not item_id.startswith(f"{entry.key}-"):
        raise HTTPException(
            status_code=404, detail=f"No item found with id {item_id!r}"
        )


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
    valid_summaries: list[ItemSummary] = [
        ItemSummary(**_item_summary(i)) for i in items
    ]

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
    "/projects/{project_id}/validate",
    response_model=ValidationReportOut,
)
def validate_project(request: Request, project_id: str) -> ValidationReportOut:
    entry = _registry_entry(request, project_id)
    ws = _paths(entry)
    return ValidationReportOut(**validate_workspace(ws).to_dict())


@router.get(
    "/projects/{project_id}/items/{item_id}",
    response_model=ItemDetail,
)
def get_item_detail(request: Request, project_id: str, item_id: str) -> ItemDetail:
    entry = _registry_entry(request, project_id)
    _require_item_in_project(entry, item_id)
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
    _require_item_in_project(entry, item_id)
    ws = _paths(entry)
    fields = body.model_dump(exclude_unset=True)
    item = item_svc.update_item(ws, item_id, **fields)
    return ItemDetail(**_item_detail(item, ws))


@router.get("/ui-state", response_model=UIStateOut)
def get_ui_state(request: Request) -> UIStateOut:
    state = ui_state_svc.load_ui_state()
    return UIStateOut(last_opened_project_id=state.last_opened_project_id)


@router.patch("/ui-state", response_model=UIStateOut)
def patch_ui_state(request: Request, body: UIStatePatch) -> UIStateOut:
    registry_dir: str = request.app.state.registry_dir
    fields = body.model_dump(exclude_unset=True)
    last_opened_project_id = fields.get("last_opened_project_id")

    if last_opened_project_id is not None:
        found = False
        for entry in registry_list(Path(registry_dir)):
            if entry.id == last_opened_project_id and entry.active:
                found = True
                break
        if not found:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown or inactive project: {last_opened_project_id!r}",
            )

    current = ui_state_svc.load_ui_state()
    if "last_opened_project_id" in fields:
        current.last_opened_project_id = last_opened_project_id
        ui_state_svc.save_ui_state(current)
    return UIStateOut(last_opened_project_id=current.last_opened_project_id)
