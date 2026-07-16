import type { ItemSummary } from "../types";
import { ITEM_TYPES, PRIORITIES } from "../types";
import { PRIORITY_LABELS, TYPE_LABELS } from "../types/labels";
import type { DropdownOption } from "./DropdownSelect";

export type TimeRange = "all" | "last_7_days" | "last_14_days" | "last_30_days";

export type TimeField = "updated_at" | "created_at";

export const TIME_RANGE_DAYS: Record<Exclude<TimeRange, "all">, number> = {
  last_7_days: 7,
  last_14_days: 14,
  last_30_days: 30,
};

export const TYPE_FILTER_OPTIONS: DropdownOption[] = [
  { value: "", label: "All types" },
  ...ITEM_TYPES.map((type) => ({
    value: type,
    label: TYPE_LABELS[type],
  })),
];

export const PRIORITY_FILTER_OPTIONS: DropdownOption[] = [
  { value: "", label: "All priorities" },
  ...PRIORITIES.map((priority) => ({
    value: priority,
    label: PRIORITY_LABELS[priority],
  })),
];

export const UPDATED_FILTER_OPTIONS: DropdownOption<TimeRange>[] = [
  { value: "all", label: "Any time" },
  { value: "last_7_days", label: "Last 7 days" },
  { value: "last_14_days", label: "Last 14 days" },
  { value: "last_30_days", label: "Last 30 days" },
];

export const CREATED_FILTER_OPTIONS: DropdownOption<TimeRange>[] = [
  { value: "all", label: "Any time" },
  { value: "last_7_days", label: "Last 7 days" },
  { value: "last_14_days", label: "Last 14 days" },
  { value: "last_30_days", label: "Last 30 days" },
];

export const DEFAULT_BOARD_FILTERS = {
  type: "",
  priority: "",
  updatedRange: "all" as TimeRange,
  createdRange: "all" as TimeRange,
};

export type BoardFilters = typeof DEFAULT_BOARD_FILTERS;

export function filterReferenceTimeForItems(
  items: ItemSummary[] | undefined,
  now?: Date,
): Date {
  if (now) return now;

  const latestItemTime =
    items?.reduce((latest, item) => {
      const timestamps = [item.created_at, item.updated_at]
        .map((value) => (value ? new Date(value).getTime() : Number.NaN))
        .filter((value) => !Number.isNaN(value));
      if (timestamps.length === 0) return latest;
      return Math.max(latest, ...timestamps);
    }, Number.NEGATIVE_INFINITY) ?? Number.NEGATIVE_INFINITY;

  return new Date(Math.max(Date.now(), latestItemTime));
}

export function isWithinTimeRange(
  item: ItemSummary,
  timeRange: TimeRange,
  field: TimeField,
  now: Date,
): boolean {
  if (timeRange === "all") return true;
  const value = item[field];
  if (!value) return false;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return false;
  const days = TIME_RANGE_DAYS[timeRange];
  const earliest = now.getTime() - days * 24 * 60 * 60 * 1000;
  return date.getTime() >= earliest && date.getTime() <= now.getTime();
}
