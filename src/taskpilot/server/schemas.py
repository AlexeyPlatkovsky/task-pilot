from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from taskpilot.core.models import Item


class ProjectSummary(BaseModel):
    id: str
    key: str
    name: str
    active: bool


class CommentOut(BaseModel):
    schema_version: int
    created_at: str
    created_by: str | None = None
    body: str


class ValidationFindingOut(BaseModel):
    severity: str
    code: str
    path: str
    field: str | None = None
    item_id: str | None = None
    message: str


class ValidationSummaryOut(BaseModel):
    errors: int
    warnings: int


class ValidationReportOut(BaseModel):
    ok: bool
    summary: ValidationSummaryOut
    findings: list[ValidationFindingOut]


class ItemSummary(BaseModel):
    id: str
    title: str
    type: str
    status: str
    priority: str
    created_at: str | None = None
    updated_at: str | None = None
    parent_id: str | None = None
    valid: bool = True
    findings: list[ValidationFindingOut] = []


class ItemDetail(Item):
    """Full item representation returned by detail and patch endpoints.

    Extends the domain Item with API-only fields: comments (populated from the
    comment service) and validity metadata (valid flag + findings).  The config
    override drops extra=allow so unknown YAML fields never leak into responses.
    """

    model_config = ConfigDict(
        extra="ignore", use_enum_values=True, validate_default=True
    )

    comments: list[CommentOut] = []
    valid: bool = True
    findings: list[ValidationFindingOut] = []


class ItemUpdateInput(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None


class UIStateOut(BaseModel):
    last_opened_project_id: str | None = None


class UIStatePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    last_opened_project_id: str | None = None
