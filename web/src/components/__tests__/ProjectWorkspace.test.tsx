import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ItemSummary } from "../../types";
import { ProjectWorkspace, type ViewMode } from "../ProjectWorkspace";

const mockFetchItems = vi.fn();
const mockFetchValidationReport = vi.fn();

vi.mock("../../api", () => ({
  fetchItems: (...args: unknown[]) => mockFetchItems(...args),
  fetchValidationReport: (...args: unknown[]) =>
    mockFetchValidationReport(...args),
}));

vi.mock("../KanbanBoard", () => ({
  KanbanBoard: ({ projectId }: { projectId: string }) => (
    <div>Board view for {projectId}</div>
  ),
}));

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
    expect(screen.getByRole("tree", { name: "Item hierarchy" })).toBeInTheDocument();

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
    await user.selectOptions(screen.getByLabelText("Status"), "done");
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
});
