export const ITEM_TYPES = ["epic", "feature", "task", "bug"] as const;
export type ItemType = (typeof ITEM_TYPES)[number];

export const STATUSES = [
  "backlog",
  "ready",
  "in_progress",
  "done",
  "cancelled",
  "deleted",
] as const;
export type Status = (typeof STATUSES)[number];

export const EDITABLE_STATUSES = [
  "backlog",
  "ready",
  "in_progress",
  "done",
  "cancelled",
] as const;
export type EditableStatus = (typeof EDITABLE_STATUSES)[number];

export const WORKFLOW_STATUSES: readonly Status[] = [
  "backlog",
  "ready",
  "in_progress",
  "done",
  "cancelled",
];

export const PRIORITIES = ["low", "normal", "high"] as const;
export type Priority = (typeof PRIORITIES)[number];

export const LINK_TYPES = ["blocks", "relates_to"] as const;
export type LinkType = (typeof LINK_TYPES)[number];

export interface ProjectSummary {
  id: string;
  key: string;
  name: string;
  active: boolean;
}

export interface Comment {
  schema_version: number;
  created_at: string;
  created_by?: string;
  body: string;
}

export interface ItemLinks {
  blocks?: string[];
  relates_to?: string[];
}

export interface ItemSummary {
  id: string;
  title: string;
  type: ItemType;
  status: Status;
  priority: Priority;
  created_at?: string | null;
  updated_at?: string | null;
  parent_id?: string | null;
  valid: boolean;
  findings?: ValidationFinding[];
}

export interface ItemDetail {
  schema_version: number;
  id: string;
  title: string;
  priority: Priority;
  type: ItemType;
  status: Status;
  created_at: string;
  updated_at: string;
  parent_id?: string;
  tags?: string[];
  description?: string;
  attachments?: string[];
  dor?: string[];
  dod?: string[];
  links?: ItemLinks;
  created_by?: string;
  performed_by?: string;
  external_refs?: string[];
  comments: Comment[];
  valid: boolean;
  findings?: ValidationFinding[];
}

export interface ValidationFinding {
  severity: "error" | "warning";
  code: string;
  path: string;
  field?: string;
  item_id?: string;
  message: string;
}

export interface ValidationReport {
  ok: boolean;
  summary: {
    errors: number;
    warnings: number;
  };
  findings: ValidationFinding[];
}

export interface ItemUpdateInput {
  title?: string;
  description?: string;
  priority?: Priority;
  status?: Status;
}

export interface ApiError {
  detail: string;
}
