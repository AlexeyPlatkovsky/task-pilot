import { describe, expect, it } from "vitest";
import type { ItemSummary } from "../../types";
import { applyItemStatus } from "../kanban-utils";

function makeItem(overrides: Partial<ItemSummary> = {}): ItemSummary {
  return {
    id: "VP-1",
    title: "Test Item",
    type: "task",
    status: "backlog",
    priority: "normal",
    valid: true,
    findings: [],
    ...overrides,
  };
}

describe("kanban-utils", () => {
  it("moves only the dropped item to the target status in cached board data", () => {
    const items = [
      makeItem({ id: "VP-1", status: "backlog" }),
      makeItem({ id: "VP-2", status: "ready" }),
    ];

    expect(applyItemStatus(items, "VP-1", "done")).toEqual([
      makeItem({ id: "VP-1", status: "done" }),
      makeItem({ id: "VP-2", status: "ready" }),
    ]);
  });

  it("preserves item object identity for unrelated cached items", () => {
    const unchanged = makeItem({ id: "VP-2", status: "ready" });
    const items = [makeItem({ id: "VP-1", status: "backlog" }), unchanged];

    const updated = applyItemStatus(items, "VP-1", "done");

    expect(updated[1]).toBe(unchanged);
  });
});
