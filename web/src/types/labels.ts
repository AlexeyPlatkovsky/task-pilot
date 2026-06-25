import type { Status, Priority, ItemType } from "./index";

export const STATUS_LABELS: Record<Status, string> = {
  backlog: "Backlog",
  ready: "Ready",
  in_progress: "In Progress",
  done: "Done",
  cancelled: "Cancelled",
  deleted: "Deleted",
};

export const PRIORITY_LABELS: Record<Priority, string> = {
  low: "Low",
  normal: "Normal",
  high: "High",
};

export const TYPE_LABELS: Record<ItemType, string> = {
  epic: "Epic",
  feature: "Feature",
  task: "Task",
  bug: "Bug",
};

export const TYPE_ORDER: Record<string, number> = {
  epic: 0,
  feature: 1,
  task: 2,
  bug: 3,
};
