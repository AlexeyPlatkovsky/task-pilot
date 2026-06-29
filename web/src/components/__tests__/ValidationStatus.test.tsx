import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ValidationStatus } from "../ValidationStatus";
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

describe("ValidationStatus", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows nothing when projectId is null", () => {
    const { container } = render(
      <ValidationStatus projectId={null} />,
      { wrapper },
    );

    expect(container.querySelector("[data-test-id='validation-valid-state']")).toBeNull();
  });

  it("shows all-valid state when no findings exist", async () => {
    mockFetchValidationReport.mockResolvedValueOnce(report());

    render(
      <ValidationStatus projectId="voice-pilot" />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.getByText("All items valid")).toBeInTheDocument();
    });

    expect(
      screen.getByTestId("validation-valid-state"),
    ).toBeInTheDocument();
  });

  it("shows error count when findings exist", async () => {
    mockFetchValidationReport.mockResolvedValueOnce(
      report({
        ok: false,
        summary: { errors: 2, warnings: 1 },
        findings: [
          {
            severity: "error",
            code: "E1",
            path: "a.yaml",
            message: "Error 1",
          },
          {
            severity: "error",
            code: "E2",
            path: "b.yaml",
            message: "Error 2",
          },
          {
            severity: "warning",
            code: "W1",
            path: "c.yaml",
            message: "Warning 1",
          },
        ],
      }),
    );

    render(
      <ValidationStatus projectId="voice-pilot" />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.getByText("2 errs, 1 warn")).toBeInTheDocument();
    });
  });

  it("shows single error and warning correctly", async () => {
    mockFetchValidationReport.mockResolvedValueOnce(
      report({
        ok: false,
        summary: { errors: 1, warnings: 1 },
        findings: [
          {
            severity: "error",
            code: "E1",
            path: "a.yaml",
            message: "Error 1",
          },
          {
            severity: "warning",
            code: "W1",
            path: "b.yaml",
            message: "Warning 1",
          },
        ],
      }),
    );

    render(
      <ValidationStatus projectId="voice-pilot" />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.getByText("1 err, 1 warn")).toBeInTheDocument();
    });
  });
});
