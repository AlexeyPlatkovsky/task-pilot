import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProjectSelector } from "../ProjectSelector";

const mockFetchProjects = vi.fn();

vi.mock("../../api", () => ({
  fetchProjects: () => mockFetchProjects(),
}));

function renderSelector(onSelect = vi.fn(), selectedProjectId: string | null = null) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  render(
    <QueryClientProvider client={queryClient}>
      <ProjectSelector
        selectedProjectId={selectedProjectId}
        onSelect={onSelect}
      />
    </QueryClientProvider>,
  );

  return onSelect;
}

describe("ProjectSelector", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockFetchProjects.mockResolvedValue([
      {
        id: "voice-pilot",
        key: "VP",
        name: "Voice Pilot",
        active: true,
      },
      {
        id: "inactive",
        key: "IN",
        name: "Inactive",
        active: false,
      },
    ]);
  });

  it("renders project options in the shared dropdown style", async () => {
    renderSelector();

    const trigger = await screen.findByRole("button", {
      name: "Project: Select a project...",
    });
    await userEvent.setup().click(trigger);

    const menu = screen.getByRole("listbox", { name: "Project options" });
    expect(menu).toHaveAttribute("data-placement", "below");
    expect(
      screen.getByRole("option", { name: "Select a project..." }),
    ).toHaveAttribute("aria-selected", "true");
    expect(
      screen.getByRole("option", { name: "Voice Pilot (VP)" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("option", { name: "Inactive (IN)" }),
    ).not.toBeInTheDocument();
  });

  it("selects a project from the dropdown", async () => {
    const user = userEvent.setup();
    const onSelect = renderSelector();

    await user.click(
      await screen.findByRole("button", {
        name: "Project: Select a project...",
      }),
    );
    await user.click(screen.getByRole("option", { name: "Voice Pilot (VP)" }));

    await waitFor(() => {
      expect(onSelect).toHaveBeenCalledWith("voice-pilot");
    });
  });
});
