from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request

from taskpilot.cli.registry import list_projects as registry_list
from taskpilot.core.layout import WorkspacePaths
from taskpilot.server.schemas import ProjectSummary

router = APIRouter(tags=["projects"])


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
