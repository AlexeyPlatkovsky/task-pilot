import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
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
    archived: false,
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

  it("renders Linked to as a one-column tokenized link list", () => {
    expect(modalCss).toContain(".relationshipList");
    expect(modalCss).toContain("grid-template-columns: minmax(0, 1fr);");
    expect(modalCss).toContain(".relationshipLink");
    expect(modalCss).toContain("color: var(--accent);");
    expect(modalCss).toContain("text-overflow: ellipsis;");
    expect(modalCss).toContain(".relationshipId");
    expect(modalCss).toContain("font-weight: var(--font-weight-semibold);");
  });

  it("gives the relationship row's status badge its own grid column, outside the truncating link (TP-111, spec 0007)", () => {
    expect(modalCss).toContain(
      "grid-template-columns: max-content max-content minmax(0, 1fr) max-content;",
    );
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
        relationships: {
          parent: {
            id: "VP-0",
            title: "Beta release",
            type: "epic",
            status: "ready",
            priority: "high",
            valid: true,
          },
          children: [
            {
              id: "VP-4",
              title: "Modal QA task",
              type: "task",
              status: "backlog",
              priority: "normal",
              valid: true,
            },
          ],
          blocks: [
            {
              id: "VP-9",
              title: "Legacy modal",
              type: "bug",
              status: "in_progress",
              priority: "high",
              valid: true,
            },
          ],
          blocked_by: [
            {
              id: "VP-6",
              title: "API contract",
              type: "task",
              status: "ready",
              priority: "normal",
              valid: true,
            },
          ],
          relates_to: [
            {
              id: "VP-7",
              title: "Workspace layout",
              type: "feature",
              status: "done",
              priority: "normal",
              valid: true,
            },
          ],
          related_to: [
            {
              id: "VP-8",
              title: "Review notes",
              type: "task",
              status: "backlog",
              priority: "low",
              valid: true,
            },
          ],
        },
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
    // Scoped to the summary: "In Progress" also appears on a Linked to row's
    // status badge (VP-9 Legacy modal, also in_progress) once that renders.
    const itemSummary = screen.getByLabelText("Item summary");
    expect(within(itemSummary).getByText("In Progress")).toBeInTheDocument();
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
    expect(screen.getByRole("heading", { name: "Linked to" })).toBeInTheDocument();
    const linkedTo = screen.getByTestId("item-modal-linked-to");
    const rows = within(linkedTo).getAllByRole("listitem");
    // Each row's status badge (TP-111, spec 0007) renders ahead of the ID/title
    // link but outside it, so the link's own accessible name is unaffected.
    expect(rows.map((row) => row.textContent)).toEqual([
      "Parent: ReadyVP-0 Beta release",
      "Child: BacklogVP-4 Modal QA task",
      "Blocks: In ProgressVP-9 Legacy modal",
      "Blocked by: ReadyVP-6 API contract",
      "Related to: DoneVP-7 Workspace layout",
      "Related to: BacklogVP-8 Review notes",
    ]);
    expect(within(linkedTo).getByRole("link", { name: "VP-0 Beta release" })).toBeInTheDocument();
    expect(within(linkedTo).getByRole("link", { name: "VP-4 Modal QA task" })).toBeInTheDocument();
    expect(within(linkedTo).getByRole("link", { name: "VP-9 Legacy modal" })).toBeInTheDocument();
    expect(within(linkedTo).getByRole("link", { name: "VP-6 API contract" })).toBeInTheDocument();
    expect(within(linkedTo).getByRole("link", { name: "VP-7 Workspace layout" })).toBeInTheDocument();
    expect(within(linkedTo).getByRole("link", { name: "VP-8 Review notes" })).toBeInTheDocument();
    expect(within(linkedTo).getAllByText("Ready")).toHaveLength(2);
    expect(within(linkedTo).getAllByText("Backlog")).toHaveLength(2);
    expect(within(linkedTo).getByText("In Progress")).toBeInTheDocument();
    expect(within(linkedTo).getByText("Done")).toBeInTheDocument();
    expect(screen.queryByText("Relates to")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Audit" })).not.toBeInTheDocument();
    expect(screen.getByText("Looks good.")).toBeInTheDocument();
  });

  it("opens a linked item in the same modal when a relationship link is clicked", async () => {
    const user = userEvent.setup();
    mockFetchItem
      .mockResolvedValueOnce(
        makeItem({
          relationships: {
            parent: {
              id: "VP-0",
              title: "Beta release",
              type: "epic",
              status: "ready",
              priority: "high",
              valid: true,
            },
            children: [],
            blocks: [],
            blocked_by: [],
            relates_to: [],
            related_to: [],
          },
        }),
      )
      .mockResolvedValueOnce(
        makeItem({
          id: "VP-0",
          title: "Loaded parent detail",
          type: "epic",
          status: "ready",
          priority: "high",
          relationships: {
            parent: null,
            children: [],
            blocks: [],
            blocked_by: [],
            relates_to: [],
            related_to: [],
          },
        }),
      );

    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );

    const link = await screen.findByRole("link", { name: "VP-0 Beta release" });
    await user.click(link);

    await waitFor(() => {
      expect(mockFetchItem).toHaveBeenLastCalledWith("VP", "VP-0");
    });
    expect(
      await screen.findByRole("heading", { name: "Epic VP-0 Loaded parent detail" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Beta release")).not.toBeInTheDocument();
  });

  it("trims long relationship titles in link rows", async () => {
    const longTitle =
      "This related item title is intentionally long enough to exceed the relationship row display limit by a wide margin";
    const trimmedTitle = `${longTitle.slice(0, 77)}...`;
    mockFetchItem.mockResolvedValueOnce(
      makeItem({
        relationships: {
          parent: null,
          children: [],
          blocks: [],
          blocked_by: [],
          relates_to: [
            {
              id: "VP-80",
              title: longTitle,
              type: "feature",
              status: "backlog",
              priority: "normal",
              valid: true,
            },
          ],
          related_to: [],
        },
      }),
    );

    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );

    const link = await screen.findByRole("link", {
      name: `VP-80 ${trimmedTitle}`,
    });
    expect(link).toHaveAttribute("title", `VP-80 ${longTitle}`);
    expect(screen.queryByText(longTitle)).not.toBeInTheDocument();
    // The status badge sits outside the truncating link, so a long title
    // still trims correctly with the badge present (spec 0007 AC3). Scoped
    // to the Linked to section: the item's own summary status is also
    // "backlog" by default, so an unscoped query would be ambiguous once
    // the relationship-row badge renders too.
    const linkedTo = screen.getByTestId("item-modal-linked-to");
    expect(within(linkedTo).getByText("Backlog")).toBeInTheDocument();
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
    expect(screen.getByText("No linked items.")).toBeInTheDocument();
    expect(screen.getByText("No comments")).toBeInTheDocument();
  });

  it("keeps missing linked items visible in the relationship section", async () => {
    mockFetchItem.mockResolvedValueOnce(
      makeItem({
        relationships: {
          parent: {
            id: "VP-404",
            title: "[missing item]",
            type: "unknown",
            status: "unknown",
            priority: "unknown",
            valid: false,
          },
          children: [],
          blocks: [
            {
              id: "VP-405",
              title: "[missing item]",
              type: "unknown",
              status: "unknown",
              priority: "unknown",
              valid: false,
            },
          ],
          blocked_by: [],
          relates_to: [],
          related_to: [],
        },
      }),
    );
    render(
      <ItemModal projectId="VP" itemId="VP-1" onClose={vi.fn()} />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Linked to" })).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: "VP-404 [missing item]" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "VP-405 [missing item]" })).toBeInTheDocument();
    expect(screen.getAllByText("missing or invalid")).toHaveLength(2);
    // TP-111/spec 0007: an invalid/missing target's placeholder "unknown"
    // status is not a real workflow state, so no status badge renders for it
    // — "missing or invalid" above remains the sole state signal for the row.
    const linkedTo = screen.getByTestId("item-modal-linked-to");
    expect(linkedTo.querySelectorAll(".statusBadge")).toHaveLength(0);
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

    expect(screen.getByTestId("item-modal-VP-1")).toBeVisible();
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
