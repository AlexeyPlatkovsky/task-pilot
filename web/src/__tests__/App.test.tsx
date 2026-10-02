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
const mockUnregisterProject = vi.fn();
const mockFetchDoctorPlan = vi.fn();

vi.mock("../api", () => ({
  fetchProjects: (...args: unknown[]) => mockFetchProjects(...args),
  fetchItems: (...args: unknown[]) => mockFetchItems(...args),
  fetchValidationReport: (...args: unknown[]) =>
    mockFetchValidationReport(...args),
  fetchUIState: (...args: unknown[]) => mockFetchUIState(...args),
  patchUIState: (...args: unknown[]) => mockPatchUIState(...args),
  unregisterProject: (...args: unknown[]) => mockUnregisterProject(...args),
  fetchDoctorPlan: (...args: unknown[]) => mockFetchDoctorPlan(...args),
  applyDoctorFixes: vi.fn(),
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

  it("loads UI state before loading projects on startup", async () => {
    let resolveUIState:
      | ((state: { last_opened_project_id: string | null }) => void)
      | undefined;
    mockFetchUIState.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveUIState = resolve;
      }),
    );

    renderApp();

    expect(mockFetchUIState).toHaveBeenCalledOnce();
    expect(mockFetchProjects).not.toHaveBeenCalled();

    resolveUIState?.({ last_opened_project_id: null });

    await waitFor(() => {
      expect(mockFetchProjects).toHaveBeenCalledOnce();
    });
  });

  describe("header project actions", () => {
    const second = { id: "alpha", key: "AL", name: "Alpha", active: true };

    it("shows only the theme toggle while no project is selected", async () => {
      renderApp();

      await screen.findByRole("button", { name: "Project: Select a project..." });
      expect(screen.getByRole("radiogroup", { name: "Theme" })).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Doctor" })).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: "Unregister project" }),
      ).not.toBeInTheDocument();
    });

    it("orders Doctor, Unregister, then the theme toggle once a project is selected", async () => {
      mockFetchUIState.mockResolvedValue({ last_opened_project_id: "voice-pilot" });
      renderApp();

      const doctor = await screen.findByRole("button", { name: "Doctor" });
      const unregister = screen.getByRole("button", { name: "Unregister project" });
      expect(doctor).toHaveAttribute("data-test-id", "header-doctor-button");
      expect(unregister).toHaveAttribute("data-test-id", "header-unregister-button");
      const theme = screen.getByRole("radiogroup", { name: "Theme" });
      expect(
        doctor.compareDocumentPosition(unregister) & Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
      expect(
        unregister.compareDocumentPosition(theme) & Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
    });

    it("opens the Doctor dialog for the selected project", async () => {
      const user = userEvent.setup();
      mockFetchUIState.mockResolvedValue({ last_opened_project_id: "voice-pilot" });
      mockFetchDoctorPlan.mockResolvedValue({ fixes: [], manual: [] });
      renderApp();

      await user.click(await screen.findByRole("button", { name: "Doctor" }));

      expect(await screen.findByRole("dialog", { name: "Doctor" })).toBeInTheDocument();
      expect(mockFetchDoctorPlan).toHaveBeenCalledWith("voice-pilot");
    });

    it("after unregistering selects the first remaining project", async () => {
      const user = userEvent.setup();
      mockFetchUIState.mockResolvedValue({ last_opened_project_id: "voice-pilot" });
      const zeta = { id: "zeta", key: "ZE", name: "Zeta", active: true };
      mockFetchProjects
        .mockResolvedValueOnce([
          second,
          { id: "voice-pilot", key: "VP", name: "Voice Pilot", active: true },
          zeta,
        ])
        .mockResolvedValue([second, zeta]);
      mockUnregisterProject.mockResolvedValue({ id: "voice-pilot" });
      renderApp();

      await user.click(
        await screen.findByRole("button", { name: "Unregister project" }),
      );
      await user.click(screen.getByRole("button", { name: "Unregister" }));

      expect(
        await screen.findByRole("button", { name: "Project: Alpha (AL)" }),
      ).toBeInTheDocument();
      expect(mockUnregisterProject).toHaveBeenCalledWith("voice-pilot");
      expect(mockPatchUIState).toHaveBeenCalledWith("alpha");
    });

    it("after unregistering the last project shows the unselected state", async () => {
      const user = userEvent.setup();
      mockFetchUIState.mockResolvedValue({ last_opened_project_id: "voice-pilot" });
      mockFetchProjects
        .mockResolvedValueOnce([{ id: "voice-pilot", key: "VP", name: "Voice Pilot", active: true }])
        .mockResolvedValue([]);
      mockUnregisterProject.mockResolvedValue({ id: "voice-pilot" });
      renderApp();

      await user.click(
        await screen.findByRole("button", { name: "Unregister project" }),
      );
      await user.click(screen.getByRole("button", { name: "Unregister" }));

      await waitFor(() =>
        expect(
          screen.queryByRole("button", { name: "Unregister project" }),
        ).not.toBeInTheDocument(),
      );
      expect(await screen.findByText(/No projects registered/)).toBeInTheDocument();
    });
    it("keeps known projects when the refresh after unregister fails", async () => {
      const user = userEvent.setup();
      mockFetchUIState.mockResolvedValue({ last_opened_project_id: "voice-pilot" });
      mockFetchProjects
        .mockResolvedValueOnce([
          second,
          { id: "voice-pilot", key: "VP", name: "Voice Pilot", active: true },
        ])
        .mockRejectedValue(new Error("offline"));
      mockUnregisterProject.mockResolvedValue({ id: "voice-pilot" });
      renderApp();

      await user.click(
        await screen.findByRole("button", { name: "Unregister project" }),
      );
      await user.click(screen.getByRole("button", { name: "Unregister" }));

      expect(
        await screen.findByRole("button", { name: "Project: Alpha (AL)" }),
      ).toBeInTheDocument();
    });
  });
});
