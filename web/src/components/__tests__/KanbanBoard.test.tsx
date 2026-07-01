import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { KanbanBoard } from "../KanbanBoard";
import { resolveDropTarget } from "../kanban-utils";
import type { ItemSummary } from "../../types";

const mockFetchItems = vi.fn();
const mockUpdateItem = vi.fn();

vi.mock("../../api", () => ({
  fetchItems: (...args: unknown[]) => mockFetchItems(...args),
  updateItem: (...args: unknown[]) => mockUpdateItem(...args),
}));

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

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows a loading spinner while items are being fetched", () => {
    mockFetchItems.mockReturnValue(new Promise(() => {}));
    render(<KanbanBoard projectId="VP" />, { wrapper });
    const spinner = screen.getByRole("status", { name: "Loading items..." });
    expect(spinner).toBeInTheDocument();
  });

  it("shows error state with retry button when fetch fails", async () => {
    mockFetchItems.mockRejectedValueOnce(new Error("Network error"));
    render(<KanbanBoard projectId="VP" />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText("Failed to load items")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("shows empty prompt when project has zero items", async () => {
    mockFetchItems.mockResolvedValueOnce([]);
    render(<KanbanBoard projectId="VP" />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText("No items yet.")).toBeInTheDocument();
    });
    expect(
      screen.getByText(/taskpilot item create/),
    ).toBeInTheDocument();
  });

  it("renders all five workflow columns", async () => {
    mockFetchItems.mockResolvedValueOnce([]);
    render(<KanbanBoard projectId="VP" />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText("Backlog")).toBeInTheDocument();
    });
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("In Progress")).toBeInTheDocument();
    expect(screen.getByText("Done")).toBeInTheDocument();
    expect(screen.getByText("Cancelled")).toBeInTheDocument();
  });

  it("distributes items into correct columns", async () => {
    mockFetchItems.mockResolvedValueOnce([
      makeItem({ id: "VP-1", status: "backlog", title: "Backlog Item" }),
      makeItem({ id: "VP-2", status: "done", title: "Done Item" }),
    ]);
    render(<KanbanBoard projectId="VP" />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText("Backlog Item")).toBeInTheDocument();
    });
    expect(screen.getByText("Done Item")).toBeInTheDocument();
  });

  it("sorts items by type then numeric ID within each column", async () => {
    mockFetchItems.mockResolvedValueOnce([
      makeItem({ id: "VP-3", type: "task", status: "backlog" }),
      makeItem({ id: "VP-1", type: "epic", status: "backlog" }),
      makeItem({ id: "VP-2", type: "feature", status: "backlog" }),
    ]);
    render(<KanbanBoard projectId="VP" />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText("VP-1")).toBeInTheDocument();
    });
    const backlogColumn = screen.getByText("Backlog").closest("[data-status]")!;
    const cards = backlogColumn.querySelectorAll("[data-item-id]");
    expect(cards[0]?.getAttribute("data-item-id")).toBe("VP-1");
    expect(cards[1]?.getAttribute("data-item-id")).toBe("VP-2");
    expect(cards[2]?.getAttribute("data-item-id")).toBe("VP-3");
  });

  it("does not show deleted items on the board", async () => {
    mockFetchItems.mockResolvedValueOnce([
      makeItem({ id: "VP-1", status: "deleted", title: "Deleted Item" }),
    ]);
    render(<KanbanBoard projectId="VP" />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText("No items yet.")).toBeInTheDocument();
    });
    expect(screen.queryByText("Deleted Item")).not.toBeInTheDocument();
  });

  it("does not allow dragging invalid items", async () => {
    mockFetchItems.mockResolvedValueOnce([
      makeItem({ id: "VP-1", status: "backlog", valid: false }),
      makeItem({ id: "VP-2", status: "ready" }),
    ]);
    render(<KanbanBoard projectId="VP" />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText("VP-1")).toBeInTheDocument();
    });

    const allButtons = screen.getAllByRole("button");
    const vp1Sortables = allButtons.filter((el) =>
      el.getAttribute("aria-roledescription") === "sortable" &&
      el.textContent?.includes("VP-1"),
    );
    const disabledOnes = vp1Sortables.filter(
      (el) => el.getAttribute("aria-disabled") === "true",
    );
    expect(disabledOnes.length).toBe(1);
    expect(vp1Sortables.length).toBe(1);
  });

  describe("board filters", () => {
    async function selectBoardFilterOption(
      user: ReturnType<typeof userEvent.setup>,
      filterLabel: string,
      optionLabel: string,
    ) {
      await user.click(
        screen.getByRole("button", { name: new RegExp(`^${filterLabel}:`) }),
      );
      await user.click(screen.getByRole("option", { name: optionLabel }));
    }

    it("renders filter bar with type, priority, updated, and created dropdowns above the board", async () => {
      mockFetchItems.mockResolvedValueOnce([
        makeItem({ id: "VP-1", title: "Test", created_at: "2026-06-25T10:00:00Z", updated_at: "2026-06-25T10:00:00Z" }),
      ]);
      render(<KanbanBoard projectId="VP" />, { wrapper });
      await waitFor(() => {
        expect(screen.getByTestId("kanban-board-filters")).toBeInTheDocument();
      });
      expect(screen.getByRole("button", { name: /^Type:/ })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^Priority:/ })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^Updated:/ })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /^Created:/ })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Clear filters" })).toBeInTheDocument();
    });

    it("filters cards by type", async () => {
      const user = userEvent.setup();
      mockFetchItems.mockResolvedValueOnce([
        makeItem({ id: "VP-1", title: "Bug item", type: "bug", created_at: "2026-06-25T10:00:00Z", updated_at: "2026-06-25T10:00:00Z" }),
        makeItem({ id: "VP-2", title: "Task item", type: "task", created_at: "2026-06-25T10:00:00Z", updated_at: "2026-06-25T10:00:00Z" }),
      ]);
      render(<KanbanBoard projectId="VP" />, { wrapper });
      await waitFor(() => {
        expect(screen.getByText("Bug item")).toBeInTheDocument();
      });

      await selectBoardFilterOption(user, "Type", "Bug");

      expect(screen.getByText("Bug item")).toBeInTheDocument();
      expect(screen.queryByText("Task item")).not.toBeInTheDocument();
    });

    it("filters cards by priority", async () => {
      const user = userEvent.setup();
      mockFetchItems.mockResolvedValueOnce([
        makeItem({ id: "VP-1", title: "High item", priority: "high", created_at: "2026-06-25T10:00:00Z", updated_at: "2026-06-25T10:00:00Z" }),
        makeItem({ id: "VP-2", title: "Low item", priority: "low", created_at: "2026-06-25T10:00:00Z", updated_at: "2026-06-25T10:00:00Z" }),
      ]);
      render(<KanbanBoard projectId="VP" />, { wrapper });
      await waitFor(() => {
        expect(screen.getByText("High item")).toBeInTheDocument();
      });

      await selectBoardFilterOption(user, "Priority", "High");

      expect(screen.getByText("High item")).toBeInTheDocument();
      expect(screen.queryByText("Low item")).not.toBeInTheDocument();
    });

    it("filters cards by updated time range", async () => {
      const user = userEvent.setup();
      mockFetchItems.mockResolvedValueOnce([
        makeItem({ id: "VP-1", title: "Recent", updated_at: "2026-06-25T10:00:00Z", created_at: "2026-06-25T10:00:00Z" }),
        makeItem({ id: "VP-2", title: "Old", updated_at: "2026-05-20T10:00:00Z", created_at: "2026-06-25T10:00:00Z" }),
      ]);
      render(
        <KanbanBoard projectId="VP" now={new Date("2026-06-28T00:00:00Z")} />,
        { wrapper },
      );
      await waitFor(() => {
        expect(screen.getByText("Recent")).toBeInTheDocument();
      });

      await selectBoardFilterOption(user, "Updated", "Last 7 days");

      expect(screen.getByText("Recent")).toBeInTheDocument();
      expect(screen.queryByText("Old")).not.toBeInTheDocument();
    });

    it("filters cards by created time range", async () => {
      const user = userEvent.setup();
      mockFetchItems.mockResolvedValueOnce([
        makeItem({ id: "VP-1", title: "Recent creation", created_at: "2026-06-25T10:00:00Z", updated_at: "2026-06-25T10:00:00Z" }),
        makeItem({ id: "VP-2", title: "Old creation", created_at: "2026-05-20T10:00:00Z", updated_at: "2026-06-25T10:00:00Z" }),
      ]);
      render(
        <KanbanBoard projectId="VP" now={new Date("2026-06-28T00:00:00Z")} />,
        { wrapper },
      );
      await waitFor(() => {
        expect(screen.getByText("Recent creation")).toBeInTheDocument();
      });

      await selectBoardFilterOption(user, "Created", "Last 7 days");

      expect(screen.getByText("Recent creation")).toBeInTheDocument();
      expect(screen.queryByText("Old creation")).not.toBeInTheDocument();
    });

    it("combines type, priority, and date filters", async () => {
      const user = userEvent.setup();
      mockFetchItems.mockResolvedValueOnce([
        makeItem({ id: "VP-1", title: "Match", type: "bug", priority: "high", updated_at: "2026-06-25T10:00:00Z", created_at: "2026-06-25T10:00:00Z" }),
        makeItem({ id: "VP-2", title: "Wrong type", type: "task", priority: "high", updated_at: "2026-06-25T10:00:00Z", created_at: "2026-06-25T10:00:00Z" }),
        makeItem({ id: "VP-3", title: "Wrong priority", type: "bug", priority: "low", updated_at: "2026-06-25T10:00:00Z", created_at: "2026-06-25T10:00:00Z" }),
        makeItem({ id: "VP-4", title: "Old", type: "bug", priority: "high", updated_at: "2026-05-20T10:00:00Z", created_at: "2026-05-20T10:00:00Z" }),
      ]);
      render(
        <KanbanBoard projectId="VP" now={new Date("2026-06-28T00:00:00Z")} />,
        { wrapper },
      );
      await waitFor(() => {
        expect(screen.getByText("Match")).toBeInTheDocument();
      });

      await selectBoardFilterOption(user, "Type", "Bug");
      await selectBoardFilterOption(user, "Priority", "High");
      await selectBoardFilterOption(user, "Updated", "Last 7 days");
      await selectBoardFilterOption(user, "Created", "Last 7 days");

      expect(screen.getByText("Match")).toBeInTheDocument();
      expect(screen.queryByText("Wrong type")).not.toBeInTheDocument();
      expect(screen.queryByText("Wrong priority")).not.toBeInTheDocument();
      expect(screen.queryByText("Old")).not.toBeInTheDocument();
    });

    it("clears all filters and restores all cards", async () => {
      const user = userEvent.setup();
      mockFetchItems.mockResolvedValueOnce([
        makeItem({ id: "VP-1", title: "Bug", type: "bug", priority: "high", updated_at: "2026-06-25T10:00:00Z", created_at: "2026-06-25T10:00:00Z" }),
        makeItem({ id: "VP-2", title: "Task", type: "task", priority: "low", updated_at: "2026-06-25T10:00:00Z", created_at: "2026-06-25T10:00:00Z" }),
      ]);
      render(
        <KanbanBoard projectId="VP" now={new Date("2026-06-28T00:00:00Z")} />,
        { wrapper },
      );
      await waitFor(() => {
        expect(screen.getByText("Bug")).toBeInTheDocument();
      });

      await selectBoardFilterOption(user, "Type", "Bug");
      expect(screen.queryByText("Task")).not.toBeInTheDocument();

      await user.click(screen.getByRole("button", { name: "Clear filters" }));

      expect(screen.getByText("Bug")).toBeInTheDocument();
      expect(screen.getByText("Task")).toBeInTheDocument();
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

    it("shows all five columns even when no cards match filters", async () => {
      const user = userEvent.setup();
      mockFetchItems.mockResolvedValueOnce([
        makeItem({ id: "VP-1", title: "Bug", type: "bug", created_at: "2026-06-25T10:00:00Z", updated_at: "2026-06-25T10:00:00Z" }),
      ]);
      render(<KanbanBoard projectId="VP" />, { wrapper });
      await waitFor(() => {
        expect(screen.getByText("Bug")).toBeInTheDocument();
      });

      await selectBoardFilterOption(user, "Type", "Task");

      expect(screen.getByTestId("kanban-column-backlog")).toBeInTheDocument();
      expect(screen.getByTestId("kanban-column-ready")).toBeInTheDocument();
      expect(screen.getByTestId("kanban-column-in_progress")).toBeInTheDocument();
      expect(screen.getByTestId("kanban-column-done")).toBeInTheDocument();
      expect(screen.getByTestId("kanban-column-cancelled")).toBeInTheDocument();
      expect(screen.getByTestId("kanban-filtered-empty")).toBeInTheDocument();
      expect(screen.getByText("No items match the selected filters.")).toBeInTheDocument();
    });

    it("does not change item status or column when filtering", async () => {
      const user = userEvent.setup();
      mockFetchItems.mockResolvedValueOnce([
        makeItem({ id: "VP-1", title: "Done bug", type: "bug", status: "done", created_at: "2026-06-25T10:00:00Z", updated_at: "2026-06-25T10:00:00Z" }),
        makeItem({ id: "VP-2", title: "Backlog task", type: "task", status: "backlog", created_at: "2026-06-25T10:00:00Z", updated_at: "2026-06-25T10:00:00Z" }),
      ]);
      render(<KanbanBoard projectId="VP" />, { wrapper });
      await waitFor(() => {
        expect(screen.getByText("Done bug")).toBeInTheDocument();
      });

      await selectBoardFilterOption(user, "Type", "Bug");

      const doneColumn = screen.getByTestId("kanban-column-done");
      expect(doneColumn.querySelector("[data-item-id='VP-1']")).toBeInTheDocument();
      const backlogColumn = screen.getByTestId("kanban-column-backlog");
      expect(backlogColumn.querySelector("[data-item-id='VP-2']")).toBeNull();
    });
  });

  describe("resolveDropTarget", () => {
    it("resolves a column status ID directly", () => {
      const items: ItemSummary[] = [];
      expect(resolveDropTarget("backlog", items)).toBe("backlog");
      expect(resolveDropTarget("done", items)).toBe("done");
    });

    it("resolves a card ID to the card's column status", () => {
      const items = [
        makeItem({ id: "VP-1", status: "backlog" }),
        makeItem({ id: "VP-2", status: "ready" }),
        makeItem({ id: "VP-3", status: "done" }),
      ];
      expect(resolveDropTarget("VP-1", items)).toBe("backlog");
      expect(resolveDropTarget("VP-2", items)).toBe("ready");
      expect(resolveDropTarget("VP-3", items)).toBe("done");
    });

    it("returns undefined for unknown overId", () => {
      const items = [makeItem({ id: "VP-1", status: "backlog" })];
      expect(resolveDropTarget("nonexistent", items)).toBeUndefined();
    });

    it("returns undefined for empty items array", () => {
      expect(resolveDropTarget("VP-1", [])).toBeUndefined();
    });

    it("prefers status match over item match when both exist", () => {
      const items = [
        makeItem({ id: "backlog", status: "done" }),
      ];
      expect(resolveDropTarget("backlog", items)).toBe("backlog");
    });
  });
});
