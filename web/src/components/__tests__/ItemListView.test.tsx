import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ItemSummary } from "../../types";
import { ItemListView } from "../ItemListView";

function makeItem(overrides: Partial<ItemSummary> = {}): ItemSummary {
  return {
    id: "VP-1",
    title: "Test Item",
    type: "task",
    status: "backlog",
    priority: "normal",
    created_at: "2026-06-25T10:00:00Z",
    updated_at: "2026-06-25T11:00:00Z",
    valid: true,
    findings: [],
    ...overrides,
  };
}

describe("ItemListView", () => {
  it("renders the required list view columns and item rows", () => {
    render(
      <ItemListView
        items={[
          makeItem({ id: "VP-1", title: "Build table", type: "task" }),
          makeItem({
            id: "VP-2",
            title: "Fix parser",
            type: "bug",
            status: "done",
            priority: "high",
          }),
        ]}
        onItemClick={vi.fn()}
      />,
    );

    expect(screen.getByRole("columnheader", { name: /ID/ })).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: /Title/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: /Type/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: /Status/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: /Priority/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: /Created/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: /Updated/ }),
    ).toBeInTheDocument();

    const rows = screen.getAllByRole("row");
    expect(within(rows[1]).getByText("VP-1")).toBeInTheDocument();
    expect(within(rows[1]).getByText("Build table")).toBeInTheDocument();
    expect(within(rows[2]).getByText("VP-2")).toBeInTheDocument();
    expect(within(rows[2]).getByText("Fix parser")).toBeInTheDocument();
  });

  it("opens an item when a valid row is clicked", async () => {
    const user = userEvent.setup();
    const onItemClick = vi.fn();
    render(
      <ItemListView
        items={[makeItem({ id: "VP-8", title: "Open row" })]}
        onItemClick={onItemClick}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Open VP-8" }));

    expect(onItemClick).toHaveBeenCalledWith("VP-8");
  });

  it("sorts rows ascending and descending when a column header is clicked", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={[
          makeItem({ id: "VP-1", title: "Second", type: "task" }),
          makeItem({ id: "VP-2", title: "First", type: "bug" }),
          makeItem({ id: "VP-3", title: "Third", type: "feature" }),
        ]}
        onItemClick={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Sort by Type/ }));

    let rows = screen.getAllByRole("row");
    expect(within(rows[1]).getByText("Bug")).toBeInTheDocument();
    expect(within(rows[2]).getByText("Feature")).toBeInTheDocument();
    expect(within(rows[3]).getByText("Task")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Sort by Type/ }));

    rows = screen.getAllByRole("row");
    expect(within(rows[1]).getByText("Task")).toBeInTheDocument();
    expect(within(rows[2]).getByText("Feature")).toBeInTheDocument();
    expect(within(rows[3]).getByText("Bug")).toBeInTheDocument();
  });

  it("filters rows by type, status, and priority together", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={[
          makeItem({
            id: "VP-1",
            title: "Completed bug",
            type: "bug",
            status: "done",
            priority: "high",
          }),
          makeItem({
            id: "VP-2",
            title: "Backlog bug",
            type: "bug",
            status: "backlog",
            priority: "high",
          }),
          makeItem({
            id: "VP-3",
            title: "Completed task",
            type: "task",
            status: "done",
            priority: "normal",
          }),
        ]}
        onItemClick={vi.fn()}
      />,
    );

    await user.selectOptions(screen.getByLabelText("Type"), "bug");
    await user.selectOptions(screen.getByLabelText("Status"), "done");
    await user.selectOptions(screen.getByLabelText("Priority"), "high");

    expect(screen.getByText("Completed bug")).toBeInTheDocument();
    expect(screen.queryByText("Backlog bug")).not.toBeInTheDocument();
    expect(screen.queryByText("Completed task")).not.toBeInTheDocument();
  });

  it("filters rows by updated time range", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={[
          makeItem({
            id: "VP-1",
            title: "Recent item",
            updated_at: "2026-06-24T10:00:00Z",
          }),
          makeItem({
            id: "VP-2",
            title: "Old item",
            updated_at: "2026-05-20T10:00:00Z",
          }),
        ]}
        now={new Date("2026-06-28T00:00:00Z")}
        onItemClick={vi.fn()}
      />,
    );

    await user.selectOptions(screen.getByLabelText("Updated"), "last_7_days");

    expect(screen.getByText("Recent item")).toBeInTheDocument();
    expect(screen.queryByText("Old item")).not.toBeInTheDocument();
  });
});
