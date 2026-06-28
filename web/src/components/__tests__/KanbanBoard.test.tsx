import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
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
