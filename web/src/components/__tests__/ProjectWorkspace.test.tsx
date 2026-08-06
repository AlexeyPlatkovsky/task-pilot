import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ItemDetail, ItemSummary } from "../../types";
import { ProjectWorkspace, ViewTabs, type ViewMode } from "../ProjectWorkspace";

const mockFetchItems = vi.fn();
const mockFetchArchivedItems = vi.fn();
const mockFetchItem = vi.fn();
const mockFetchValidationReport = vi.fn();

vi.mock("../../api", () => ({
  fetchItems: (...args: unknown[]) => mockFetchItems(...args),
  fetchArchivedItems: (...args: unknown[]) => mockFetchArchivedItems(...args),
  fetchItem: (...args: unknown[]) => mockFetchItem(...args),
  fetchValidationReport: (...args: unknown[]) =>
    mockFetchValidationReport(...args),
}));

vi.mock("../KanbanBoard", () => ({
  KanbanBoard: ({ projectId }: { projectId: string }) => (
    <div>Board view for {projectId}</div>
  ),
}));

function makeItem(overrides: Partial<ItemSummary> = {}): ItemSummary {
  const now = new Date().toISOString();
  return {
    id: "VP-1",
    title: "Test Item",
    type: "task",
    status: "backlog",
    priority: "normal",
    valid: true,
    findings: [],
    created_at: now,
    updated_at: now,
    ...overrides,
  };
}

function makeItemDetail(overrides: Partial<ItemDetail> = {}): ItemDetail {
  return {
    ...makeItem(),
    archived: false,
    comments: [],
    relationships: {
      parent: null,
      children: [],
      blocks: [],
      blocked_by: [],
      relates_to: [],
      related_to: [],
    },
    ...overrides,
  };
}

function renderWorkspace(
  projectId = "voice-pilot",
  activeView: ViewMode = "board",
) {
  const qc = createQueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <ProjectWorkspace projectId={projectId} activeView={activeView} />
    </QueryClientProvider>,
  );
}

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

describe("ProjectWorkspace", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockFetchValidationReport.mockResolvedValue({
      ok: true,
      summary: { errors: 0, warnings: 0 },
      findings: [],
    });
    mockFetchItems.mockResolvedValue([
      makeItem({ id: "VP-1", title: "Root epic", type: "epic" }),
      makeItem({
        id: "VP-2",
        title: "Child feature",
        type: "feature",
        parent_id: "VP-1",
      }),
    ]);
    mockFetchArchivedItems.mockResolvedValue([]);
    mockFetchItem.mockResolvedValue(makeItemDetail());
  });

  it("switches between Board, List, and Tree views for the same project", async () => {
    const view = renderWorkspace();

    expect(screen.getByText("Board view for voice-pilot")).toBeInTheDocument();

    view.rerender(
      <QueryClientProvider client={createQueryClient()}>
        <ProjectWorkspace projectId="voice-pilot" activeView="list" />
      </QueryClientProvider>,
    );
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Open VP-1" })).toBeInTheDocument();
    });
    expect(mockFetchItems).toHaveBeenCalledWith("voice-pilot");

    view.rerender(
      <QueryClientProvider client={createQueryClient()}>
        <ProjectWorkspace projectId="voice-pilot" activeView="tree" />
      </QueryClientProvider>,
    );
    await waitFor(() => {
      expect(screen.getByRole("tree", { name: "Item hierarchy" })).toBeInTheDocument();
    });

    view.rerender(
      <QueryClientProvider client={createQueryClient()}>
        <ProjectWorkspace projectId="voice-pilot" activeView="board" />
      </QueryClientProvider>,
    );
    expect(screen.getByText("Board view for voice-pilot")).toBeInTheDocument();
  });

  it("clears list filters when the selected project changes", async () => {
    const user = userEvent.setup();
    mockFetchItems.mockImplementation((projectId: string) =>
      Promise.resolve([
        makeItem({
          id: projectId === "alpha" ? "AL-1" : "BT-1",
          title: projectId === "alpha" ? "Alpha backlog" : "Beta backlog",
          status: "backlog",
        }),
      ]),
    );

    const view = renderWorkspace("alpha", "list");

    await waitFor(() => {
      expect(screen.getByText("Alpha backlog")).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: "Status: All statuses" }));
    await user.click(screen.getByRole("option", { name: "Done" }));
    expect(
      screen.getByText("No items match the selected filters."),
    ).toBeInTheDocument();

    view.rerender(
      <QueryClientProvider
        client={createQueryClient()}
      >
        <ProjectWorkspace projectId="beta" activeView="list" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("Beta backlog")).toBeInTheDocument();
    });
  });

  it("renders archived children with active parents in the Tree without changing List", async () => {
    const user = userEvent.setup();
    mockFetchItems.mockResolvedValue([
      makeItem({ id: "VP-1", title: "Active epic", type: "epic" }),
    ]);
    mockFetchArchivedItems.mockResolvedValue([
      makeItem({
        id: "VP-2",
        title: "Archived task",
        type: "task",
        status: "done",
        parent_id: "VP-1",
      }),
    ]);

    const view = renderWorkspace("voice-pilot", "tree");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Open VP-1" })).toBeInTheDocument();
    });
    expect(mockFetchArchivedItems).toHaveBeenCalledWith("voice-pilot");
    await user.click(screen.getByRole("button", { name: "Expand VP-1" }));
    expect(screen.getByRole("button", { name: "Open VP-2" })).toBeInTheDocument();
    mockFetchItem.mockResolvedValue(
      makeItemDetail({
        id: "VP-2",
        title: "Archived task",
        type: "task",
        status: "done",
      }),
    );
    await user.click(screen.getByRole("button", { name: "Open VP-2" }));
    await waitFor(() => {
      expect(screen.getByTestId("item-modal-VP-2")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Close" }));

    mockFetchArchivedItems.mockClear();
    view.rerender(
      <QueryClientProvider client={createQueryClient()}>
        <ProjectWorkspace projectId="voice-pilot" activeView="list" />
      </QueryClientProvider>,
    );
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Open VP-1" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Open VP-2" })).not.toBeInTheDocument();
    expect(mockFetchArchivedItems).not.toHaveBeenCalled();
  });

  it("does not carry a Tree archive-fetch failure into List", async () => {
    mockFetchItems.mockResolvedValue([
      makeItem({ id: "VP-1", title: "Active epic", type: "epic" }),
    ]);
    mockFetchArchivedItems.mockRejectedValue(new Error("archive unavailable"));
    const view = renderWorkspace("voice-pilot", "tree");

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Failed to load items");
    });

    view.rerender(
      <QueryClientProvider client={createQueryClient()}>
        <ProjectWorkspace projectId="voice-pilot" activeView="list" />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Open VP-1" })).toBeInTheDocument();
    });
  });

  it("makes an archived relationship target read-only from an active List item", async () => {
    const user = userEvent.setup();
    mockFetchItems.mockResolvedValue([
      makeItem({ id: "VP-1", title: "Active task", type: "task" }),
    ]);
    mockFetchItem.mockImplementation((_projectId: string, itemId: string) => {
      if (itemId === "VP-1") {
        return Promise.resolve(
          makeItemDetail({
            id: "VP-1",
            title: "Active task",
            relationships: {
              parent: {
                id: "VP-2",
                title: "Archived feature",
                type: "feature",
                status: "done",
                priority: "normal",
                valid: true,
              },
              children: [],
              blocks: [],
              blocked_by: [],
              relates_to: [],
              related_to: [],
            },
          }),
        );
      }
      return Promise.resolve(
        makeItemDetail({
          id: "VP-2",
          title: "Archived feature",
          status: "done",
          archived: true,
        } as Partial<ItemDetail>),
      );
    });

    renderWorkspace("voice-pilot", "list");
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Open VP-1" })).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: "Open VP-1" }));
    await user.click(screen.getByRole("link", { name: /VP-2 Archived feature/ }));
    await waitFor(() => {
      expect(screen.getByTestId("item-modal-VP-2")).toBeInTheDocument();
    });

    expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
  });
});

describe("ViewTabs", () => {
  it("always exposes Archived navigation without a visibility toggle", () => {
    render(
      <ViewTabs
        activeView="board"
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByRole("tab", { name: "Archived" })).toBeVisible();
    expect(screen.queryByTestId("workspace-toggle-archived")).not.toBeInTheDocument();
  });
});
