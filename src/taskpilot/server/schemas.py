from __future__ import annotations

from pydantic import BaseModel


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


class ItemLinksOut(BaseModel):
    blocks: list[str] = []
    relates_to: list[str] = []


class ItemSummary(BaseModel):
    id: str
    title: str
    type: str
    status: str
    priority: str
    valid: bool = True
    findings: list[ValidationFindingOut] | None = None


class ItemDetail(BaseModel):
    schema_version: int
    id: str
    title: str
    priority: str
    type: str
    status: str
    created_at: str
    updated_at: str
    parent_id: str | None = None
    tags: list[str] | None = None
    description: str | None = None
    attachments: list[str] | None = None
    dor: list[str] | None = None
    dod: list[str] | None = None
    links: ItemLinksOut | None = None
    created_by: str | None = None
    performed_by: str | None = None
    external_refs: list[str] | None = None
    comments: list[CommentOut] = []
    valid: bool = True
    findings: list[ValidationFindingOut] | None = None


class ItemUpdateInput(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
