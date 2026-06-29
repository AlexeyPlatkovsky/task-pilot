import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ItemSummary } from "../../types";
import { ItemTreeView } from "../ItemTreeView";

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

describe("ItemTreeView", () => {
  it("renders parent and child items through expandable hierarchy", async () => {
    const user = userEvent.setup();
    render(
      <ItemTreeView
        items={[
          makeItem({ id: "VP-1", title: "Epic", type: "epic" }),
          makeItem({
            id: "VP-2",
            title: "Feature",
            type: "feature",
            parent_id: "VP-1",
          }),
          makeItem({
            id: "VP-3",
            title: "Task",
            type: "task",
            parent_id: "VP-2",
          }),
        ]}
        onItemClick={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Open VP-1" })).toBeInTheDocument();
    expect(screen.queryByText("Feature")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Expand VP-1" }));

    expect(screen.getByRole("button", { name: "Open VP-2" })).toBeInTheDocument();
    expect(screen.queryByText("Task")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Expand VP-2" }));

    expect(screen.getByRole("button", { name: "Open VP-3" })).toBeInTheDocument();
  });

  it("opens a valid tree item from its title button", async () => {
    const user = userEvent.setup();
    const onItemClick = vi.fn();
    render(
      <ItemTreeView
        items={[makeItem({ id: "VP-5", title: "Open me", type: "epic" })]}
        onItemClick={onItemClick}
      />,
    );

    const row = screen.getByRole("treeitem", { name: /VP-5/ });
    await user.click(within(row).getByRole("button", { name: "Open VP-5" }));

    expect(onItemClick).toHaveBeenCalledWith("VP-5");
  });
});
