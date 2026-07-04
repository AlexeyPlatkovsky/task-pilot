import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { readFileSync } from "node:fs";
import { ItemModal } from "../ItemModal";
import type { ItemDetail, ItemType } from "../../types";

const modalCss = readFileSync("src/components/ItemModal.module.css", "utf8");

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
    expect(screen.getByRole("heading", { name: "VP-1 Item Detail" })).toBeInTheDocument();
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

  it("renders the item header with type before a prominent item id", async () => {
    mockFetchItem.mockResolvedValueOnce(makeItem());
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => {
      expect(screen.getByText("TASK")).toBeInTheDocument();
    });
    const title = screen.getByRole("heading", {
      name: "Task VP-1 Test Item",
    });
    const typeChip = screen.getByLabelText("Type: Task");
    const itemId = screen.getByText("VP-1");
    expect(title).toContainElement(typeChip);
    expect(title).toContainElement(itemId);
    expect(document.body.querySelector(".itemId")).not.toBeNull();
  });

  const typeIconCases: Array<[ItemType, string, string]> = [
    ["epic", "EPIC", "Epic"],
    ["feature", "FEAT", "Feature"],
    ["task", "TASK", "Task"],
    ["bug", "BUG", "Bug"],
  ];

  it.each(typeIconCases)(
    "renders a same-size icon label for %s items",
    async (type, shortLabel, iconLabel) => {
      mockFetchItem.mockResolvedValueOnce(makeItem({ type }));
      render(
        <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
        { wrapper },
      );
      await waitFor(() => {
        expect(screen.getByText(shortLabel)).toBeInTheDocument();
      });
      expect(
        document.body.querySelector(`svg[aria-label="${iconLabel}"]`),
      ).not.toBeNull();
      expect(document.body.querySelector(`.type-${type}`)).not.toBeNull();
    },
  );

  it("keeps type labels visually aligned and tokenized like item cards", () => {
    expect(modalCss).toContain(".typeBadge");
    expect(modalCss).toContain("font-size: var(--font-size-xs);");
    expect(modalCss).toContain("inline-size: calc(var(--space-8) + var(--space-6) + var(--space-2));");
    expect(modalCss).toContain("padding: 0.125rem 0.375rem;");
    expect(modalCss).toContain(".type-epic");
    expect(modalCss).toContain("background: var(--type-epic-bg);");
    expect(modalCss).toContain("color: var(--type-epic-fg);");
    expect(modalCss).toContain(".type-feature");
    expect(modalCss).toContain("background: var(--type-feature-bg);");
    expect(modalCss).toContain("color: var(--type-feature-fg);");
    expect(modalCss).toContain(".type-task");
    expect(modalCss).toContain("background: var(--type-task-bg);");
    expect(modalCss).toContain("color: var(--type-task-fg);");
    expect(modalCss).toContain(".type-bug");
    expect(modalCss).toContain("background: var(--type-bug-bg);");
    expect(modalCss).toContain("color: var(--type-bug-fg);");
  });

  it("keeps header actions in the top-right and summary in two columns", () => {
    expect(modalCss).toContain(".headerActions");
    expect(modalCss).toContain("position: absolute;");
    expect(modalCss).toContain("top: var(--space-4);");
    expect(modalCss).toContain("right: var(--space-4);");
    expect(modalCss).toContain("grid-template-columns: repeat(2, minmax(0, 1fr));");
  });

  it("renders item summary metadata in two labelled columns", async () => {
    mockFetchItem.mockResolvedValueOnce(makeItem());
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );

    const summary = await screen.findByLabelText("Item summary");
    expect(summary).toHaveTextContent("Priority");
    expect(summary).toHaveTextContent("Normal");
    expect(summary).toHaveTextContent("Status");
    expect(summary).toHaveTextContent("Backlog");
    expect(summary).toHaveTextContent("Created");
    expect(summary).toHaveTextContent("Updated");
    expect(summary.querySelectorAll(".summaryColumn")).toHaveLength(2);
    expect(summary.querySelector('time[datetime="2026-01-01T00:00:00Z"]')).not.toBeNull();
  });

  it("groups the full item detail context for scanning", async () => {
    mockFetchItem.mockResolvedValueOnce(
      makeItem({
        title: "Ship Beta item detail",
        type: "feature",
        status: "in_progress",
        priority: "high",
        description: "Review **modal** hierarchy.",
        parent_id: "VP-0",
        links: {
          blocks: ["VP-9"],
          relates_to: ["VP-7"],
        },
        tags: ["beta", "ui"],
        dor: ["Information architecture accepted"],
        dod: ["Component tests pass"],
        attachments: ["docs/modal.png"],
        external_refs: ["https://example.test/spec"],
        created_by: "Aleksei",
        performed_by: "Codex",
        comments: [
          {
            schema_version: 1,
            created_at: "2026-01-02T00:00:00Z",
            created_by: "Aleksei",
            body: "Looks good.",
          },
        ],
      }),
    );

    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.getByText("Ship Beta item detail")).toBeInTheDocument();
    });
    expect(screen.getByText("VP-1")).toBeInTheDocument();
    expect(screen.getByText("FEAT")).toBeInTheDocument();
    expect(screen.getByText("In Progress")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "Info" })).toBeInTheDocument();
    expect(screen.getByText("Description")).toBeInTheDocument();
    expect(screen.getByText("modal")).toBeInTheDocument();
    expect(screen.getByText("Readiness")).toBeInTheDocument();
    expect(screen.getByText("Information architecture accepted")).toBeInTheDocument();
    expect(screen.getByText("Component tests pass")).toBeInTheDocument();
    expect(screen.getByText("Resources")).toBeInTheDocument();
    expect(screen.getByText("beta")).toBeInTheDocument();
    expect(screen.getByText("docs/modal.png")).toBeInTheDocument();
    expect(screen.getByText("https://example.test/spec")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Relationships" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Audit" })).not.toBeInTheDocument();
    expect(screen.getByText("Looks good.")).toBeInTheDocument();
  });

  it("shows explicit empty states for absent optional groups", async () => {
    mockFetchItem.mockResolvedValueOnce(makeItem());
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.getByText("No description yet.")).toBeInTheDocument();
    });
    expect(screen.getByText("No Definition of Ready items.")).toBeInTheDocument();
    expect(screen.getByText("No Definition of Done items.")).toBeInTheDocument();
    expect(screen.getByText("No tags, attachments, or links.")).toBeInTheDocument();
    expect(screen.getByText("No comments")).toBeInTheDocument();
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

  it("shows icon-only Edit and Delete buttons in the header action group", async () => {
    mockFetchItem.mockResolvedValueOnce(makeItem());
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );
    const editButton = await screen.findByRole("button", { name: "Edit" });
    const deleteButton = screen.getByRole("button", { name: "Delete" });
    expect(editButton).toHaveTextContent("");
    expect(deleteButton).toHaveTextContent("");
    expect(document.body.querySelector(".headerActions")).toContainElement(editButton);
    expect(document.body.querySelector(".headerActions")).toContainElement(deleteButton);
  });

  it("opens the existing delete confirmation from view mode", async () => {
    const user = userEvent.setup();
    mockFetchItem.mockResolvedValueOnce(makeItem());
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );

    await user.click(await screen.findByRole("button", { name: "Delete" }));

    expect(
      screen.getByRole("alertdialog", { name: "Delete this item?" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/status to "deleted"/)).toBeInTheDocument();
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
      expect(screen.getByText("TASK")).toBeInTheDocument();
    });
    // Radix Dialog uses a Portal that appends to document.body, outside the render container
    const closeSvg = document.body.querySelector('svg[aria-label="Close"]');
    expect(closeSvg).not.toBeNull();
  });
});
