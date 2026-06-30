import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  ITEM_TYPES,
  PRIORITIES,
  WORKFLOW_STATUSES,
  type ItemSummary,
} from "../../types";
import {
  PRIORITY_LABELS,
  STATUS_LABELS,
  TYPE_LABELS,
} from "../../types/labels";
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

function visibleRowIds(): string[] {
  return screen
    .queryAllByTestId("item-list-row")
    .map((row) => row.getAttribute("data-item-id"))
    .filter((id): id is string => id !== null);
}

async function selectFilterOption(
  user: ReturnType<typeof userEvent.setup>,
  filterLabel: string,
  optionLabel: string,
) {
  await user.click(
    screen.getByRole("button", { name: new RegExp(`^${filterLabel}:`) }),
  );
  await user.click(screen.getByRole("option", { name: optionLabel }));
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

    const sortByType = screen.getByRole("button", {
      name: "Sort by Type (not sorted)",
    });

    expect(within(sortByType).getByText("△▽")).toBeInTheDocument();

    await user.click(sortByType);
    expect(sortByType).toHaveAccessibleName("Sort by Type (ascending)");
    expect(within(sortByType).getByText("▲▽")).toBeInTheDocument();

    let rows = screen.getAllByRole("row");
    expect(within(rows[1]).getByText("Bug")).toBeInTheDocument();
    expect(within(rows[2]).getByText("Feature")).toBeInTheDocument();
    expect(within(rows[3]).getByText("Task")).toBeInTheDocument();

    await user.click(sortByType);
    expect(sortByType).toHaveAccessibleName("Sort by Type (descending)");
    expect(within(sortByType).getByText("△▼")).toBeInTheDocument();

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

    await selectFilterOption(user, "Type", "Bug");
    await selectFilterOption(user, "Status", "Done");
    await selectFilterOption(user, "Priority", "High");

    expect(screen.getByText("Completed bug")).toBeInTheDocument();
    expect(screen.queryByText("Backlog bug")).not.toBeInTheDocument();
    expect(screen.queryByText("Completed task")).not.toBeInTheDocument();
  });

  it("filters rows for every status option without blocking further interactions", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={WORKFLOW_STATUSES.map((status, index) =>
          makeItem({
            id: `VP-${index + 1}`,
            title: `${status} item`,
            status,
          }),
        )}
        onItemClick={vi.fn()}
      />,
    );

    for (const [index, status] of WORKFLOW_STATUSES.entries()) {
      await selectFilterOption(user, "Status", STATUS_LABELS[status]);
      expect(visibleRowIds()).toEqual([`VP-${index + 1}`]);
    }

    await selectFilterOption(user, "Status", "All statuses");
    await user.click(
      screen.getByRole("button", { name: "Sort by ID (not sorted)" }),
    );

    expect(visibleRowIds()).toEqual(["VP-1", "VP-2", "VP-3", "VP-4", "VP-5"]);
  });

  it("filters rows for every type option", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={ITEM_TYPES.map((type, index) =>
          makeItem({
            id: `VP-${index + 1}`,
            title: `${type} item`,
            type,
          }),
        )}
        onItemClick={vi.fn()}
      />,
    );

    for (const [index, type] of ITEM_TYPES.entries()) {
      await selectFilterOption(user, "Type", TYPE_LABELS[type]);
      expect(visibleRowIds()).toEqual([`VP-${index + 1}`]);
    }
  });

  it("filters rows for every priority option", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={PRIORITIES.map((priority, index) =>
          makeItem({
            id: `VP-${index + 1}`,
            title: `${priority} item`,
            priority,
          }),
        )}
        onItemClick={vi.fn()}
      />,
    );

    for (const [index, priority] of PRIORITIES.entries()) {
      await selectFilterOption(user, "Priority", PRIORITY_LABELS[priority]);
      expect(visibleRowIds()).toEqual([`VP-${index + 1}`]);
    }
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

    await selectFilterOption(user, "Updated", "Last 7 days");

    expect(screen.getByText("Recent item")).toBeInTheDocument();
    expect(screen.queryByText("Old item")).not.toBeInTheDocument();
  });

  it("filters rows for every updated time range option", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={[
          makeItem({
            id: "VP-1",
            title: "Within 7 days",
            updated_at: "2026-06-25T10:00:00Z",
          }),
          makeItem({
            id: "VP-2",
            title: "Within 14 days",
            updated_at: "2026-06-18T10:00:00Z",
          }),
          makeItem({
            id: "VP-3",
            title: "Within 30 days",
            updated_at: "2026-06-01T10:00:00Z",
          }),
          makeItem({
            id: "VP-4",
            title: "Older item",
            updated_at: "2026-05-15T10:00:00Z",
          }),
        ]}
        now={new Date("2026-06-29T00:00:00Z")}
        onItemClick={vi.fn()}
      />,
    );

    await selectFilterOption(user, "Updated", "Last 7 days");
    expect(visibleRowIds()).toEqual(["VP-1"]);

    await selectFilterOption(user, "Updated", "Last 14 days");
    expect(visibleRowIds()).toEqual(["VP-1", "VP-2"]);

    await selectFilterOption(user, "Updated", "Last 30 days");
    expect(visibleRowIds()).toEqual(["VP-1", "VP-2", "VP-3"]);

    await selectFilterOption(user, "Updated", "Any time");
    expect(visibleRowIds()).toEqual(["VP-1", "VP-2", "VP-3", "VP-4"]);
  });

  it("filters rows by created time range", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={[
          makeItem({
            id: "VP-1",
            title: "Recent creation",
            created_at: "2026-06-25T10:00:00Z",
            updated_at: "2026-06-25T10:00:00Z",
          }),
          makeItem({
            id: "VP-2",
            title: "Old creation",
            created_at: "2026-05-20T10:00:00Z",
            updated_at: "2026-06-25T10:00:00Z",
          }),
        ]}
        now={new Date("2026-06-28T00:00:00Z")}
        onItemClick={vi.fn()}
      />,
    );

    await selectFilterOption(user, "Created", "Last 7 days");

    expect(screen.getByText("Recent creation")).toBeInTheDocument();
    expect(screen.queryByText("Old creation")).not.toBeInTheDocument();
  });

  it("combines updated and created range filters", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={[
          makeItem({
            id: "VP-1",
            title: "Both recent",
            created_at: "2026-06-25T10:00:00Z",
            updated_at: "2026-06-25T10:00:00Z",
          }),
          makeItem({
            id: "VP-2",
            title: "Old created",
            created_at: "2026-05-20T10:00:00Z",
            updated_at: "2026-06-25T10:00:00Z",
          }),
          makeItem({
            id: "VP-3",
            title: "Old updated",
            created_at: "2026-06-25T10:00:00Z",
            updated_at: "2026-05-20T10:00:00Z",
          }),
        ]}
        now={new Date("2026-06-28T00:00:00Z")}
        onItemClick={vi.fn()}
      />,
    );

    await selectFilterOption(user, "Created", "Last 7 days");
    await selectFilterOption(user, "Updated", "Last 7 days");

    expect(screen.getByText("Both recent")).toBeInTheDocument();
    expect(screen.queryByText("Old created")).not.toBeInTheDocument();
    expect(screen.queryByText("Old updated")).not.toBeInTheDocument();
  });

  it("renders a selected filter menu below the filter control", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={[
          makeItem({ id: "VP-1", title: "Backlog item", status: "backlog" }),
          makeItem({ id: "VP-2", title: "Done item", status: "done" }),
        ]}
        onItemClick={vi.fn()}
      />,
    );

    await selectFilterOption(user, "Status", "Done");
    await user.click(screen.getByRole("button", { name: "Status: Done" }));

    expect(
      screen.getByRole("listbox", { name: "Status options" }),
    ).toHaveAttribute("data-placement", "below");
  });

  it("renders filter labels and dropdowns on one row with clear at the right edge", () => {
    render(
      <ItemListView
        items={[makeItem({ id: "VP-1", title: "Visible item" })]}
        onItemClick={vi.fn()}
      />,
    );

    for (const field of screen.getAllByTestId("item-list-filter-field")) {
      expect(field).toHaveAttribute("data-layout", "inline");
    }
    expect(
      screen.getByRole("button", { name: "Clear filters" }),
    ).toBeInTheDocument();
  });

  it("clears all active filters and restores the default list", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={[
          makeItem({
            id: "VP-1",
            title: "Done bug",
            type: "bug",
            status: "done",
            priority: "high",
            updated_at: "2026-06-24T10:00:00Z",
          }),
          makeItem({
            id: "VP-2",
            title: "Backlog task",
            type: "task",
            status: "backlog",
            priority: "normal",
            updated_at: "2026-05-20T10:00:00Z",
          }),
        ]}
        now={new Date("2026-06-28T00:00:00Z")}
        onItemClick={vi.fn()}
      />,
    );

    await selectFilterOption(user, "Type", "Bug");
    await selectFilterOption(user, "Status", "Done");
    await selectFilterOption(user, "Priority", "High");
    await selectFilterOption(user, "Updated", "Last 7 days");
    await selectFilterOption(user, "Created", "Last 7 days");
    expect(visibleRowIds()).toEqual(["VP-1"]);

    await user.click(screen.getByRole("button", { name: "Clear filters" }));

    expect(visibleRowIds()).toEqual(["VP-1", "VP-2"]);
    expect(
      screen.getByRole("button", { name: "Status: All statuses" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Type: All types" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Priority: All priorities" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Updated: Any time" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Created: Any time" }),
    ).toBeInTheDocument();
  });

  it("keeps the implicit current time stable while date filters remain active", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-29T00:00:00Z"));

    try {
      render(
        <ItemListView
          items={[
            makeItem({
              id: "VP-1",
              title: "Boundary item",
              updated_at: "2026-06-22T12:00:00Z",
            }),
          ]}
          onItemClick={vi.fn()}
        />,
      );

      fireEvent.click(
        screen.getByRole("button", { name: "Updated: Any time" }),
      );
      fireEvent.click(screen.getByRole("option", { name: "Last 7 days" }));
      expect(visibleRowIds()).toEqual(["VP-1"]);

      vi.setSystemTime(new Date("2026-07-02T00:00:00Z"));
      fireEvent.click(
        screen.getByRole("button", { name: "Sort by ID (not sorted)" }),
      );

      expect(visibleRowIds()).toEqual(["VP-1"]);
    } finally {
      vi.useRealTimers();
    }
  });

  it("sorts only the rows that remain after filters are applied", async () => {
    const user = userEvent.setup();
    render(
      <ItemListView
        items={[
          makeItem({
            id: "VP-1",
            title: "High bug",
            type: "bug",
            status: "done",
            priority: "high",
          }),
          makeItem({
            id: "VP-2",
            title: "Normal bug",
            type: "bug",
            status: "done",
            priority: "normal",
          }),
          makeItem({
            id: "VP-3",
            title: "High task",
            type: "task",
            status: "done",
            priority: "high",
          }),
          makeItem({
            id: "VP-4",
            title: "Backlog bug",
            type: "bug",
            status: "backlog",
            priority: "high",
          }),
        ]}
        onItemClick={vi.fn()}
      />,
    );

    await selectFilterOption(user, "Type", "Bug");
    await selectFilterOption(user, "Status", "Done");
    await user.click(
      screen.getByRole("button", { name: "Sort by Priority (not sorted)" }),
    );

    const rows = screen.getAllByRole("row");
    expect(rows).toHaveLength(3);
    expect(within(rows[1]).getByText("High bug")).toBeInTheDocument();
    expect(within(rows[2]).getByText("Normal bug")).toBeInTheDocument();
    expect(screen.queryByText("High task")).not.toBeInTheDocument();
    expect(screen.queryByText("Backlog bug")).not.toBeInTheDocument();
  });
});
