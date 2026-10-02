import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DoctorDialog } from "../DoctorDialog";
import type { DoctorPlan } from "../../types";

const mockFetchDoctorPlan = vi.fn();
const mockApplyDoctorFixes = vi.fn();

vi.mock("../../api", () => ({
  fetchDoctorPlan: (...args: unknown[]) => mockFetchDoctorPlan(...args),
  applyDoctorFixes: (...args: unknown[]) => mockApplyDoctorFixes(...args),
}));

const fix = {
  kind: "remove_link" as const,
  item_id: "VP-1",
  path: ".taskpilot/items/VP-1.yaml",
  field: "links.blocks",
  target: "VP-99",
  description: "Remove links.blocks -> VP-99 from VP-1",
};

const manual = {
  severity: "error" as const,
  code: "invalid_yaml",
  path: ".taskpilot/items/VP-5.yaml",
  message: "Invalid YAML: bad",
};

const okReport = { ok: true, summary: { errors: 0, warnings: 0 }, findings: [] };

function renderDialog() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const invalidate = vi.spyOn(queryClient, "invalidateQueries");
  const onClose = vi.fn();
  render(
    <QueryClientProvider client={queryClient}>
      <DoctorDialog projectId="voice-pilot" onClose={onClose} />
    </QueryClientProvider>,
  );
  return { onClose, invalidate };
}

describe("DoctorDialog", () => {
  beforeEach(() => vi.clearAllMocks());

  it("lists safe fixes and manual findings with counts", async () => {
    mockFetchDoctorPlan.mockResolvedValue({ fixes: [fix], manual: [manual] });
    renderDialog();

    const dialog = await screen.findByRole("dialog", { name: "Doctor" });
    expect(dialog).toHaveAttribute("data-test-id", "doctor-dialog");
    const safe = await within(dialog).findByRole("region", { name: "Safe fixes (1)" });
    expect(safe).toHaveTextContent(fix.description);
    expect(safe).toHaveTextContent(fix.path);
    expect(safe).toHaveAttribute("data-test-id", "doctor-safe-fixes");
    const manualRegion = within(dialog).getByRole("region", {
      name: "Needs manual attention (1)",
    });
    expect(manualRegion).toHaveAttribute("data-test-id", "doctor-manual-findings");
    expect(manualRegion).toHaveTextContent("error");
    expect(manualRegion).toHaveTextContent(manual.path);
    expect(manualRegion).toHaveTextContent(manual.message);
    expect(mockFetchDoctorPlan).toHaveBeenCalledWith("voice-pilot");
  });

  it("shows empty texts and disables apply when nothing is fixable", async () => {
    mockFetchDoctorPlan.mockResolvedValue({ fixes: [], manual: [] });
    renderDialog();

    expect(await screen.findByText("No automatic fixes available.")).toBeInTheDocument();
    expect(screen.getByText("Nothing else to fix.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply 0 fixes" })).toBeDisabled();
  });

  it("prefixes manual findings with their item id when known", async () => {
    mockFetchDoctorPlan.mockResolvedValue({
      fixes: [],
      manual: [{ ...manual, code: "link_to_deleted", item_id: "VP-2", severity: "warning" }],
    });
    renderDialog();

    const region = await screen.findByRole("region", {
      name: "Needs manual attention (1)",
    });
    expect(region).toHaveTextContent("VP-2");
    expect(region).toHaveTextContent("warning");
  });

  it("applies fixes, shows the count, and refreshes dependent queries", async () => {
    const user = userEvent.setup();
    const after: DoctorPlan = { fixes: [], manual: [] };
    mockFetchDoctorPlan
      .mockResolvedValueOnce({ fixes: [fix], manual: [] })
      .mockResolvedValue(after);
    mockApplyDoctorFixes.mockResolvedValue({
      applied: [fix],
      failed: [],
      report: okReport,
    });
    const { invalidate } = renderDialog();

    const apply = await screen.findByRole("button", { name: "Apply 1 fix" });
    expect(apply).toHaveAttribute("data-test-id", "doctor-apply");
    expect(screen.getByRole("button", { name: "Close" })).toHaveAttribute(
      "data-test-id",
      "doctor-close",
    );
    await user.click(apply);

    const result = await screen.findByRole("status");
    expect(result).toHaveTextContent("Applied 1 fix.");
    expect(result).toHaveAttribute("data-test-id", "doctor-apply-result");
    expect(mockApplyDoctorFixes).toHaveBeenCalledWith("voice-pilot");
    await waitFor(() =>
      expect(screen.getByText("No automatic fixes available.")).toBeInTheDocument(),
    );
    const keys = invalidate.mock.calls.map((c) => JSON.stringify(c[0]?.queryKey));
    expect(keys).toEqual(
      expect.arrayContaining([
        JSON.stringify(["items", "voice-pilot"]),
        JSON.stringify(["tree-items", "voice-pilot"]),
        JSON.stringify(["item", "voice-pilot"]),
        JSON.stringify(["validation", "voice-pilot"]),
        JSON.stringify(["doctor", "voice-pilot"]),
      ]),
    );
  });

  it("uses the plural form for several fixes", async () => {
    mockFetchDoctorPlan.mockResolvedValue({
      fixes: [fix, { ...fix, target: "VP-98", description: "Remove links.blocks -> VP-98 from VP-1" }],
      manual: [],
    });
    renderDialog();

    expect(await screen.findByRole("button", { name: "Apply 2 fixes" })).toBeEnabled();
  });

  it("shows an inline error when apply fails and keeps the list", async () => {
    const user = userEvent.setup();
    mockFetchDoctorPlan.mockResolvedValue({ fixes: [fix], manual: [] });
    mockApplyDoctorFixes.mockRejectedValue(new Error("conflict"));
    renderDialog();

    await user.click(await screen.findByRole("button", { name: "Apply 1 fix" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Failed to apply fixes: conflict",
    );
    expect(screen.getByText(fix.description)).toBeInTheDocument();
  });

  it("lists fixes the server could not apply with their reasons", async () => {
    const user = userEvent.setup();
    mockFetchDoctorPlan.mockResolvedValue({ fixes: [fix], manual: [] });
    mockApplyDoctorFixes.mockResolvedValue({
      applied: [],
      failed: [{ fix, error: "A task cannot be the parent of a task" }],
      report: okReport,
    });
    renderDialog();

    await user.click(await screen.findByRole("button", { name: "Apply 1 fix" }));

    expect(await screen.findByRole("status")).toHaveTextContent("Applied 0 fixes.");
    const alert = screen.getByRole("alert");
    expect(alert).toHaveAttribute("data-test-id", "doctor-apply-failures");
    expect(alert).toHaveTextContent("Could not apply 1 fix");
    expect(alert).toHaveTextContent(
      `${fix.description}: A task cannot be the parent of a task`,
    );
  });

  it("shows a load error that can still be closed", async () => {
    const user = userEvent.setup();
    mockFetchDoctorPlan.mockRejectedValue(new Error("down"));
    const { onClose } = renderDialog();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Failed to load diagnostics",
    );
    await user.click(screen.getByRole("button", { name: "Close" }));
    expect(onClose).toHaveBeenCalled();
  });
});
