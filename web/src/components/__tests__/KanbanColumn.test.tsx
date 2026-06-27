import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DndContext } from "@dnd-kit/core";
import { KanbanColumn } from "../KanbanColumn";
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

function Wrapper({ children }: { children: React.ReactNode }) {
  return <DndContext>{children}</DndContext>;
}

describe("KanbanColumn", () => {
  it("renders header label and item count", () => {
    render(
      <KanbanColumn
        status="backlog"
        label="Backlog"
        items={[makeItem(), makeItem({ id: "VP-2" })]}
      />,
      { wrapper: Wrapper },
    );

    expect(screen.getByText("Backlog")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("renders empty state when no items", () => {
    render(
      <KanbanColumn status="backlog" label="Backlog" items={[]} />,
      { wrapper: Wrapper },
    );

    expect(screen.getByText("No items")).toBeInTheDocument();
  });

  it("renders Kanban cards for each item", () => {
    render(
      <KanbanColumn
        status="backlog"
        label="Backlog"
        items={[
          makeItem({ id: "VP-1", title: "First" }),
          makeItem({ id: "VP-2", title: "Second" }),
        ]}
      />,
      { wrapper: Wrapper },
    );

    expect(screen.getByText("First")).toBeInTheDocument();
    expect(screen.getByText("Second")).toBeInTheDocument();
  });

  it("applies data-status attribute", () => {
    const { container } = render(
      <KanbanColumn status="done" label="Done" items={[]} />,
      { wrapper: Wrapper },
    );

    const column = container.querySelector("[data-status]");
    expect(column).not.toBeNull();
    expect(column!.getAttribute("data-status")).toBe("done");
  });

  it("renders cards in a list role", () => {
    render(
      <KanbanColumn
        status="backlog"
        label="Backlog"
        items={[makeItem()]}
      />,
      { wrapper: Wrapper },
    );

    expect(screen.getByRole("list")).toBeInTheDocument();
  });

  it("shows count badge with zero items", () => {
    render(
      <KanbanColumn status="backlog" label="Backlog" items={[]} />,
      { wrapper: Wrapper },
    );

    expect(screen.getByText("0")).toBeInTheDocument();
  });
});
