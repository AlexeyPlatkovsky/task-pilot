import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { KanbanBoard } from "../KanbanBoard";
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
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows loading state while items are being fetched", () => {
    mockFetchItems.mockReturnValue(new Promise(() => {}));
    render(<KanbanBoard projectId="VP" />, { wrapper });
    expect(screen.getByText("Loading items...")).toBeInTheDocument();
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
});
