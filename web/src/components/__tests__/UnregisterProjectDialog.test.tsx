import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { UnregisterProjectDialog } from "../UnregisterProjectDialog";

const mockUnregisterProject = vi.fn();

vi.mock("../../api", () => ({
  unregisterProject: (...args: unknown[]) => mockUnregisterProject(...args),
}));

const project = { id: "voice-pilot", key: "VP", name: "Voice Pilot", active: true };

function renderDialog() {
  const onUnregistered = vi.fn();
  const onCancel = vi.fn();
  render(
    <QueryClientProvider client={new QueryClient()}>
      <UnregisterProjectDialog
        project={project}
        onUnregistered={onUnregistered}
        onCancel={onCancel}
      />
    </QueryClientProvider>,
  );
  return { onUnregistered, onCancel };
}

describe("UnregisterProjectDialog", () => {
  beforeEach(() => vi.clearAllMocks());

  it("names the project and states that files on disk are kept", () => {
    renderDialog();

    const dialog = screen.getByRole("alertdialog", {
      name: "Unregister Voice Pilot?",
    });
    expect(dialog).toHaveAttribute("data-test-id", "unregister-project-dialog");
    expect(dialog).toHaveTextContent(".taskpilot/");
    expect(dialog).toHaveTextContent(/kept/i);
    expect(dialog).toHaveTextContent("taskpilot init");
  });

  it("cancel calls onCancel without calling the API", async () => {
    const user = userEvent.setup();
    const { onCancel, onUnregistered } = renderDialog();

    const cancel = screen.getByRole("button", { name: "Cancel" });
    expect(cancel).toHaveAttribute("data-test-id", "unregister-project-cancel");
    expect(screen.getByRole("button", { name: "Unregister" })).toHaveAttribute(
      "data-test-id",
      "unregister-project-submit",
    );
    await user.click(cancel);

    expect(onCancel).toHaveBeenCalled();
    expect(onUnregistered).not.toHaveBeenCalled();
    expect(mockUnregisterProject).not.toHaveBeenCalled();
  });

  it("confirm unregisters and reports the removed id", async () => {
    const user = userEvent.setup();
    mockUnregisterProject.mockResolvedValue(project);
    const { onUnregistered } = renderDialog();

    await user.click(screen.getByRole("button", { name: "Unregister" }));

    await waitFor(() => expect(onUnregistered).toHaveBeenCalledWith("voice-pilot"));
    expect(mockUnregisterProject).toHaveBeenCalledWith("voice-pilot");
  });

  it("shows pending text while the request is in flight", async () => {
    const user = userEvent.setup();
    mockUnregisterProject.mockReturnValue(new Promise(() => {}));
    renderDialog();

    await user.click(screen.getByRole("button", { name: "Unregister" }));

    expect(
      await screen.findByRole("button", { name: "Unregistering..." }),
    ).toBeDisabled();
  });

  it("keeps the dialog open with an inline error on failure", async () => {
    const user = userEvent.setup();
    mockUnregisterProject.mockRejectedValue(new Error("boom"));
    const { onUnregistered } = renderDialog();

    await user.click(screen.getByRole("button", { name: "Unregister" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Failed to unregister project",
    );
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(onUnregistered).not.toHaveBeenCalled();
  });

  it("ignores Escape while pending and still shows a later failure", async () => {
    const user = userEvent.setup();
    let reject: (reason: unknown) => void = () => {};
    mockUnregisterProject.mockReturnValue(
      new Promise((_, r) => {
        reject = r;
      }),
    );
    const { onCancel } = renderDialog();

    await user.click(screen.getByRole("button", { name: "Unregister" }));
    await user.keyboard("{Escape}");

    expect(onCancel).not.toHaveBeenCalled();
    reject(new Error("boom"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Failed to unregister project",
    );
  });

  it("calls onCancel once when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const { onCancel } = renderDialog();

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
