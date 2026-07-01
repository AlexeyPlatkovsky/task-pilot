import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ItemModal } from "../ItemModal";
import type { ItemDetail } from "../../types";

const mockFetchItem = vi.fn();
const mockUpdateItem = vi.fn();

vi.mock("../../api", () => ({
  fetchItem: (...args: unknown[]) => mockFetchItem(...args),
  updateItem: (...args: unknown[]) => mockUpdateItem(...args),
}));

function makeItem(overrides: Partial<ItemDetail> = {}): ItemDetail {
  return {
    schema_version: 1,
    id: "VP-1",
    title: "Test Item",
    type: "task",
    status: "backlog",
    priority: "normal",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    valid: true,
    comments: [],
    ...overrides,
  };
}

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("ItemModal", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows loading state while item is being fetched", () => {
    mockFetchItem.mockReturnValue(new Promise(() => {}));
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );
    expect(screen.getByText("Loading item...")).toBeInTheDocument();
  });

  it("shows error state with retry button when fetch fails", async () => {
    mockFetchItem.mockRejectedValueOnce(new Error("Network error"));
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => {
      expect(screen.getByText("Failed to load item")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("does not render when itemId is null", () => {
    mockFetchItem.mockRejectedValueOnce(new Error("should not be called"));
    const { container } = render(
      <ItemModal projectId="VP" itemId={null} onClose={vi.fn()} />,
      { wrapper },
    );
    expect(container.querySelector("[role='dialog']")).toBeNull();
  });

  it("renders item detail view with badges", async () => {
    mockFetchItem.mockResolvedValueOnce(makeItem());
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => {
      expect(screen.getByText("Task")).toBeInTheDocument();
    });
    expect(screen.getByText("Backlog")).toBeInTheDocument();
    expect(screen.getByText("Normal")).toBeInTheDocument();
  });

  it("renders description as Markdown HTML", async () => {
    mockFetchItem.mockResolvedValueOnce(
      makeItem({ description: "**bold** `code`" }),
    );
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => {
      expect(screen.getByText("Description")).toBeInTheDocument();
    });
    expect(screen.getByText("bold")).toBeInTheDocument();
    expect(screen.getByText("code")).toBeInTheDocument();
  });

  it("shows comment thread when comments exist", async () => {
    mockFetchItem.mockResolvedValueOnce(
      makeItem({
        comments: [
          {
            schema_version: 1,
            created_at: "2026-01-01T00:00:00Z",
            body: "First comment",
          },
        ],
      }),
    );
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => {
      expect(screen.getByText("Comments")).toBeInTheDocument();
    });
    expect(screen.getByText("First comment")).toBeInTheDocument();
  });

  it("shows Edit button in read mode", async () => {
    mockFetchItem.mockResolvedValueOnce(makeItem());
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
    });
  });

  it("keeps dirty edit fields while refreshing clean fields after item refetch", async () => {
    const user = userEvent.setup();
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    mockFetchItem
      .mockResolvedValueOnce(
        makeItem({
          title: "Initial title",
          priority: "normal",
          status: "backlog",
        }),
      )
      .mockResolvedValueOnce(
        makeItem({
          title: "Server title",
          priority: "high",
          status: "done",
        }),
      );

    render(
      <QueryClientProvider client={queryClient}>
        <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />
      </QueryClientProvider>,
    );
    await user.click(await screen.findByRole("button", { name: "Edit" }));

    const titleInput = screen.getByLabelText("Title");
    await user.clear(titleInput);
    await user.type(titleInput, "Local draft title");

    await queryClient.invalidateQueries({
      queryKey: ["item", "VP", "VP-1"],
    });

    await waitFor(() => {
      expect(mockFetchItem).toHaveBeenCalledTimes(2);
      expect(screen.getByLabelText("Priority")).toHaveValue("high");
      expect(screen.getByLabelText("Status")).toHaveValue("done");
    });
    expect(screen.getByLabelText("Title")).toHaveValue("Local draft title");
  });

  it("shows validation findings for invalid items", async () => {
    mockFetchItem.mockResolvedValueOnce(
      makeItem({
        valid: false,
        findings: [
          {
            severity: "error",
            code: "E001",
            path: "/title",
            field: "title",
            message: "Title is required",
          },
        ],
      }),
    );
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => {
      expect(screen.getByText("Validation Issues")).toBeInTheDocument();
    });
    expect(screen.getByText(/Title is required/)).toBeInTheDocument();
  });

  // AC-10: close button must render a Lucide SVG icon with aria-label="Close"
  it("renders close button with an SVG icon labelled Close", async () => {
    mockFetchItem.mockResolvedValueOnce(makeItem());
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => {
      expect(screen.getByText("Task")).toBeInTheDocument();
    });
    // Radix Dialog uses a Portal that appends to document.body, outside the render container
    const closeSvg = document.body.querySelector('svg[aria-label="Close"]');
    expect(closeSvg).not.toBeNull();
  });
});
