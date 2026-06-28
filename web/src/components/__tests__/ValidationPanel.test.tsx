import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ValidationPanel } from "../ValidationPanel";
import type { ValidationReport } from "../../types";

const mockFetchValidationReport = vi.fn();

vi.mock("../../api", () => ({
  fetchValidationReport: (...args: unknown[]) =>
    mockFetchValidationReport(...args),
}));

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

function report(overrides: Partial<ValidationReport> = {}): ValidationReport {
  return {
    ok: true,
    summary: { errors: 0, warnings: 0 },
    findings: [],
    ...overrides,
  };
}

describe("ValidationPanel", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows all-valid state when no findings exist", async () => {
    mockFetchValidationReport.mockResolvedValueOnce(report());

    render(
      <ValidationPanel projectId="voice-pilot" onItemClick={vi.fn()} />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.getByText("All items valid")).toBeInTheDocument();
    });
  });

  it("shows validation findings and opens linked items", async () => {
    const user = userEvent.setup();
    const onItemClick = vi.fn();
    mockFetchValidationReport.mockResolvedValueOnce(
      report({
        ok: false,
        summary: { errors: 1, warnings: 0 },
        findings: [
          {
            severity: "error",
            code: "missing_required_field",
            path: "items/VP-3.yaml",
            field: "title",
            item_id: "VP-3",
            message: "Missing required field: title",
          },
        ],
      }),
    );

    render(
      <ValidationPanel projectId="voice-pilot" onItemClick={onItemClick} />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.getByText("items/VP-3.yaml")).toBeInTheDocument();
    });
    expect(
      screen.getByText("Missing required field: title"),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Open VP-3 validation issue" }),
    );

    expect(onItemClick).toHaveBeenCalledWith("VP-3");
  });
});
