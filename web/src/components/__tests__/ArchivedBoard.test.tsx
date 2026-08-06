/** @file ArchivedBoard component tests. */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ItemDetail, ItemSummary } from "../../types";
import { ArchivedBoard } from "../ArchivedBoard";

// Mock API module
const mockFetchArchived = vi.fn();
const mockUnarchive = vi.fn();
const mockUpdate = vi.fn();
const mockFetchItem = vi.fn();

vi.mock("../../api", () => ({
  fetchArchivedItems: (...args: unknown[]) => mockFetchArchived(...args),
  unarchiveItem: (...args: unknown[]) => mockUnarchive(...args),
  updateItem: (...args: unknown[]) => mockUpdate(...args),
  fetchItems: vi.fn(),
  fetchItem: (...args: unknown[]) => mockFetchItem(...args),
  fetchValidationReport: vi.fn(),
  fetchUIState: vi.fn(),
  patchUIState: vi.fn(),
}));

function makeItem(overrides: Partial<ItemSummary> = {}): ItemSummary {
  const now = new Date().toISOString();
  return {
    id: "TP-1",
    title: "Test Item",
    type: "task",
    status: "done",
    priority: "normal",
    archived: true,
    valid: true,
    findings: [],
    created_at: now,
    updated_at: now,
    ...overrides,
  };
}

function makeDetail(overrides: Partial<ItemDetail> = {}): ItemDetail {
  const now = new Date().toISOString();
  return {
    schema_version: 1,
    id: "TP-1",
    title: "Archived Item",
    type: "task",
    status: "done",
    priority: "normal",
    valid: true,
    created_at: now,
    updated_at: now,
    comments: [],
    ...overrides,
  };
}

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={createQueryClient()}>
      {children}
    </QueryClientProvider>
  );
}

describe("ArchivedBoard", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockFetchItem.mockResolvedValue(makeDetail());
  });

  it("renders loading state when visible and loading", async () => {
    mockFetchArchived.mockReturnValue(new Promise(() => {})); // never resolves
    render(
      <Wrapper>
        <ArchivedBoard projectId="TP" />
      </Wrapper>,
    );
    expect(screen.getByText("Loading archived items...")).toBeInTheDocument();
  });

  it("renders empty prompt when no items", async () => {
    mockFetchArchived.mockResolvedValue([]);
    render(
      <Wrapper>
        <ArchivedBoard projectId="TP" />
      </Wrapper>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("archived-empty-prompt")).toBeInTheDocument();
    });
  });

  it("renders archived items", async () => {
    const items = [makeItem({ id: "TP-1", title: "Archived Item 1" })];
    mockFetchArchived.mockResolvedValue(items);
    render(
      <Wrapper>
        <ArchivedBoard projectId="TP" />
      </Wrapper>,
    );
    await waitFor(() => {
      expect(screen.getByText("Archived Item 1")).toBeInTheDocument();
    });
  });

  it("renders a plain type-first list without Kanban columns", async () => {
    mockFetchArchived.mockResolvedValue([
      makeItem({ id: "TP-4", title: "Bug", type: "bug" }),
      makeItem({ id: "TP-8", title: "Later Task", type: "task" }),
      makeItem({ id: "TP-2", title: "Feature", type: "feature" }),
      makeItem({ id: "TP-3", title: "Earlier Task", type: "task" }),
      makeItem({ id: "TP-1", title: "Epic", type: "epic" }),
    ]);

    render(
      <Wrapper>
        <ArchivedBoard projectId="TP" />
      </Wrapper>,
    );

    const rows = await screen.findAllByTestId("archived-list-row");
    expect(rows.map((row) => row.getAttribute("data-item-id"))).toEqual([
      "TP-1",
      "TP-2",
      "TP-3",
      "TP-8",
      "TP-4",
    ]);
    expect(screen.queryByTestId("kanban-column-done")).not.toBeInTheDocument();
  });

  it("opens archived item detail in read-only mode", async () => {
    mockFetchArchived.mockResolvedValue([makeItem({ title: "Archived Item" })]);
    const user = userEvent.setup();
    render(
      <Wrapper>
        <ArchivedBoard projectId="TP" />
      </Wrapper>,
    );

    await user.click(await screen.findByTestId("archived-list-open-TP-1"));

    await waitFor(() => {
      expect(mockFetchItem).toHaveBeenCalledWith("TP", "TP-1");
    });
    expect(await screen.findByTestId("item-modal-TP-1")).toHaveTextContent("Archived Item");
    expect(screen.queryByTestId("item-modal-edit")).not.toBeInTheDocument();
    expect(screen.queryByTestId("item-modal-delete")).not.toBeInTheDocument();
  });

  it("shows error state on failure", async () => {
    mockFetchArchived.mockRejectedValue(new Error("API error"));
    render(
      <Wrapper>
        <ArchivedBoard projectId="TP" isVisible={true} />
      </Wrapper>,
    );
    await waitFor(() => {
      expect(screen.getByText("Failed to load archived items")).toBeInTheDocument();
    });
    expect(screen.getByRole("alert")).toHaveTextContent("Failed to load archived items");
  });

  it("calls fetchArchivedItems with correct projectId", async () => {
    mockFetchArchived.mockResolvedValue([]);
    render(
      <Wrapper>
        <ArchivedBoard projectId="MYPROJECT" />
      </Wrapper>,
    );
    await waitFor(() => {
      expect(mockFetchArchived).toHaveBeenCalledWith("MYPROJECT");
    });
  });

  it("unarchive button calls unarchiveItem", async () => {
    const items = [makeItem({ id: "TP-1", title: "Archived Item" })];
    mockFetchArchived.mockResolvedValue(items);
    mockUnarchive.mockResolvedValue(undefined);

    const user = userEvent.setup();
    render(
      <Wrapper>
        <ArchivedBoard projectId="TP" />
      </Wrapper>,
    );

    await waitFor(() => {
      expect(screen.getByText("Archived Item")).toBeInTheDocument();
    });

    await user.click(screen.getByTestId("unarchive-button-TP-1"));
    expect(screen.getByTestId("unarchive-confirm-dialog")).toBeInTheDocument();
    await user.click(screen.getByTestId("unarchive-confirm-submit"));
    await waitFor(() => expect(mockUnarchive).toHaveBeenCalledWith("TP", "TP-1"));
  });

  it("keeps the confirmation open and allows retry after an unarchive failure", async () => {
    const items = [makeItem({ id: "TP-1", title: "Archived Item" })];
    mockFetchArchived.mockResolvedValue(items);
    let rejectRequest: (reason: Error) => void = () => {};
    mockUnarchive.mockReturnValue(new Promise((_, reject) => { rejectRequest = reject; }));
    const user = userEvent.setup();
    render(<Wrapper><ArchivedBoard projectId="TP" /></Wrapper>);
    await screen.findByText("Archived Item");
    await user.click(screen.getByTestId("unarchive-button-TP-1"));
    await user.click(screen.getByTestId("unarchive-confirm-submit"));
    expect(screen.getByTestId("unarchive-confirm-submit")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();

    rejectRequest(new Error("Active item already exists"));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Active item already exists"));
    expect(screen.getByTestId("unarchive-confirm-submit")).toBeEnabled();
    await user.click(screen.getByTestId("unarchive-confirm-submit"));
    expect(mockUnarchive).toHaveBeenCalledTimes(2);
  });
});
