import { describe, expect, it, vi } from "vitest";
import {
  filterReferenceTimeForItems,
  isWithinTimeRange,
  TIME_RANGE_DAYS,
  DEFAULT_BOARD_FILTERS,
  TYPE_FILTER_OPTIONS,
  PRIORITY_FILTER_OPTIONS,
  UPDATED_FILTER_OPTIONS,
  CREATED_FILTER_OPTIONS,
} from "../filters";
import type { ItemSummary } from "../../types";

function makeItem(overrides: Partial<ItemSummary> = {}): ItemSummary {
  return {
    id: "VP-1",
    title: "Test Item",
    type: "task",
    status: "backlog",
    priority: "normal",
    valid: true,
    ...overrides,
  };
}

const NOW = new Date("2026-06-28T00:00:00Z");

describe("isWithinTimeRange", () => {
  it("returns true when timeRange is 'all'", () => {
    const item = makeItem({ updated_at: "2020-01-01T00:00:00Z" });
    expect(isWithinTimeRange(item, "all", "updated_at", NOW)).toBe(true);
  });

  it("returns false when the field value is null", () => {
    const item = makeItem({ updated_at: null });
    expect(isWithinTimeRange(item, "last_7_days", "updated_at", NOW)).toBe(false);
  });

  it("returns false when the field value is undefined", () => {
    const item = makeItem({ updated_at: undefined });
    expect(isWithinTimeRange(item, "last_7_days", "updated_at", NOW)).toBe(false);
  });

  it("returns false when the field value is an invalid date", () => {
    const item = makeItem({ updated_at: "not-a-date" });
    expect(isWithinTimeRange(item, "last_7_days", "updated_at", NOW)).toBe(false);
  });

  it("returns true for items within last 7 days (updated_at)", () => {
    const item = makeItem({ updated_at: "2026-06-24T10:00:00Z" });
    expect(isWithinTimeRange(item, "last_7_days", "updated_at", NOW)).toBe(true);
  });

  it("returns false for items older than 7 days (updated_at)", () => {
    const item = makeItem({ updated_at: "2026-06-20T10:00:00Z" });
    expect(isWithinTimeRange(item, "last_7_days", "updated_at", NOW)).toBe(false);
  });

  it("returns true for items within last 14 days (updated_at)", () => {
    const item = makeItem({ updated_at: "2026-06-18T10:00:00Z" });
    expect(isWithinTimeRange(item, "last_7_days", "updated_at", NOW)).toBe(false);
    expect(isWithinTimeRange(item, "last_14_days", "updated_at", NOW)).toBe(true);
  });

  it("returns true for items within last 30 days (updated_at)", () => {
    const item = makeItem({ updated_at: "2026-06-01T10:00:00Z" });
    expect(isWithinTimeRange(item, "last_14_days", "updated_at", NOW)).toBe(false);
    expect(isWithinTimeRange(item, "last_30_days", "updated_at", NOW)).toBe(true);
  });

  it("returns true for items within last 7 days (created_at)", () => {
    const item = makeItem({ created_at: "2026-06-25T10:00:00Z" });
    expect(isWithinTimeRange(item, "last_7_days", "created_at", NOW)).toBe(true);
  });

  it("returns false for items older than 7 days (created_at)", () => {
    const item = makeItem({ created_at: "2026-06-15T10:00:00Z" });
    expect(isWithinTimeRange(item, "last_7_days", "created_at", NOW)).toBe(false);
  });

  it("includes items exactly at the boundary", () => {
    const sevenDaysAgo = new Date(NOW.getTime() - 7 * 24 * 60 * 60 * 1000);
    const boundaryItem = makeItem({
      created_at: sevenDaysAgo.toISOString(),
    });
    expect(
      isWithinTimeRange(boundaryItem, "last_7_days", "created_at", NOW),
    ).toBe(true);
  });

  it("excludes items one millisecond before the boundary", () => {
    const sevenDaysAgoMs = NOW.getTime() - 7 * 24 * 60 * 60 * 1000;
    const justBefore = new Date(sevenDaysAgoMs - 1);
    const boundaryItem = makeItem({
      created_at: justBefore.toISOString(),
    });
    expect(
      isWithinTimeRange(boundaryItem, "last_7_days", "created_at", NOW),
    ).toBe(false);
  });

  it("uses updated_at field independently of created_at", () => {
    const item = makeItem({
      updated_at: "2026-06-24T10:00:00Z",
      created_at: "2020-01-01T00:00:00Z",
    });
    expect(isWithinTimeRange(item, "last_7_days", "updated_at", NOW)).toBe(true);
    expect(isWithinTimeRange(item, "last_7_days", "created_at", NOW)).toBe(false);
  });
});

describe("TIME_RANGE_DAYS", () => {
  it("has the expected day counts", () => {
    expect(TIME_RANGE_DAYS.last_7_days).toBe(7);
    expect(TIME_RANGE_DAYS.last_14_days).toBe(14);
    expect(TIME_RANGE_DAYS.last_30_days).toBe(30);
  });
});

describe("filterReferenceTimeForItems", () => {
  it("uses an explicit now value when provided", () => {
    const explicitNow = new Date("2026-07-04T14:00:00Z");
    const item = makeItem({ created_at: "2026-07-04T14:05:00Z" });

    expect(filterReferenceTimeForItems([item], explicitNow)).toBe(explicitNow);
  });

  it("uses the newest item timestamp when refreshed data is newer than the local clock", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-04T14:00:00Z"));

    try {
      const referenceTime = filterReferenceTimeForItems([
        makeItem({ created_at: "2026-07-04T14:05:00Z" }),
      ]);

      expect(referenceTime.toISOString()).toBe("2026-07-04T14:05:00.000Z");
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("DEFAULT_BOARD_FILTERS", () => {
  it("has all defaults as empty string or 'all'", () => {
    expect(DEFAULT_BOARD_FILTERS.type).toBe("");
    expect(DEFAULT_BOARD_FILTERS.priority).toBe("");
    expect(DEFAULT_BOARD_FILTERS.updatedRange).toBe("all");
    expect(DEFAULT_BOARD_FILTERS.createdRange).toBe("all");
  });
});

describe("TYPE_FILTER_OPTIONS", () => {
  it("includes 'All types' as first option", () => {
    expect(TYPE_FILTER_OPTIONS[0]).toEqual({ value: "", label: "All types" });
  });

  it("includes all item types", () => {
    const typeValues = TYPE_FILTER_OPTIONS.slice(1).map((o) => o.value);
    expect(typeValues).toEqual(["epic", "feature", "task", "bug"]);
  });
});

describe("PRIORITY_FILTER_OPTIONS", () => {
  it("includes 'All priorities' as first option", () => {
    expect(PRIORITY_FILTER_OPTIONS[0]).toEqual({
      value: "",
      label: "All priorities",
    });
  });

  it("includes all priorities", () => {
    const priorityValues = PRIORITY_FILTER_OPTIONS.slice(1).map((o) => o.value);
    expect(priorityValues).toEqual(["low", "normal", "high"]);
  });
});

describe("UPDATED_FILTER_OPTIONS", () => {
  it("has the correct time range options", () => {
    const values = UPDATED_FILTER_OPTIONS.map((o) => o.value);
    expect(values).toEqual(["all", "last_7_days", "last_14_days", "last_30_days"]);
  });

  it("has the correct labels", () => {
    const labels = UPDATED_FILTER_OPTIONS.map((o) => o.label);
    expect(labels).toEqual([
      "Any time",
      "Last 7 days",
      "Last 14 days",
      "Last 30 days",
    ]);
  });
});

describe("CREATED_FILTER_OPTIONS", () => {
  it("has the same option set as UPDATED_FILTER_OPTIONS", () => {
    expect(CREATED_FILTER_OPTIONS).toEqual(UPDATED_FILTER_OPTIONS);
  });
});
