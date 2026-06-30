import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";

const mockFetchProjects = vi.fn();
const mockFetchItems = vi.fn();
const mockFetchValidationReport = vi.fn();
const mockFetchUIState = vi.fn();
const mockPatchUIState = vi.fn();

vi.mock("../api", () => ({
  fetchProjects: (...args: unknown[]) => mockFetchProjects(...args),
  fetchItems: (...args: unknown[]) => mockFetchItems(...args),
  fetchValidationReport: (...args: unknown[]) =>
    mockFetchValidationReport(...args),
  fetchUIState: (...args: unknown[]) => mockFetchUIState(...args),
  patchUIState: (...args: unknown[]) => mockPatchUIState(...args),
}));

vi.mock("../components/KanbanBoard", () => ({
  KanbanBoard: ({ projectId }: { projectId: string }) => (
    <div data-test-id="kanban-board">Board view for {projectId}</div>
  ),
}));

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  );
}

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchUIState.mockResolvedValue({ last_opened_project_id: null });
    mockPatchUIState.mockResolvedValue({ last_opened_project_id: "voice-pilot" });
    mockFetchProjects.mockResolvedValue([
      {
        id: "voice-pilot",
        key: "VP",
        name: "Voice Pilot",
        active: true,
      },
    ]);
    mockFetchItems.mockResolvedValue([]);
    mockFetchValidationReport.mockResolvedValue({
      ok: true,
      summary: { errors: 0, warnings: 0 },
      findings: [],
    });
  });

  it("places the workspace tablist in the header immediately after the project selector", async () => {
    const user = userEvent.setup();
    renderApp();

    const projectSelector = await screen.findByRole("button", {
      name: "Project: Select a project...",
    });

    expect(
      screen.queryByRole("tablist", { name: "Workspace views" }),
    ).not.toBeInTheDocument();

    await user.click(projectSelector);
    await user.click(screen.getByRole("option", { name: "Voice Pilot (VP)" }));

    const tablist = await screen.findByRole("tablist", {
      name: "Workspace views",
    });
    const selectorWrapper = screen.getByTestId("project-selector-field")
      .parentElement;

    expect(selectorWrapper).not.toBeNull();
    expect(selectorWrapper?.nextElementSibling).toBe(tablist);
    expect(tablist.closest("header")).not.toBeNull();
    await waitFor(() => {
      expect(screen.getByTestId("kanban-board")).toHaveTextContent(
        "Board view for voice-pilot",
      );
    });
  });
});
