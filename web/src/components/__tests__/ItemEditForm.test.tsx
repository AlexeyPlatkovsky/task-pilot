import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ItemEditForm } from "../ItemEditForm";
import type { ItemDetail } from "../../types";

const mockUpdateItem = vi.fn();

vi.mock("../../api", () => ({
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

describe("ItemEditForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders form with default values from item", async () => {
    const item = makeItem();
    render(
      <ItemEditForm
        projectId="VP"
        item={item}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />,
      { wrapper },
    );
    expect(screen.getByLabelText("Title")).toHaveValue("Test Item");
    expect(screen.getByLabelText("Priority")).toHaveValue("normal");
    expect(screen.getByLabelText("Status")).toHaveValue("backlog");
  });

  it("shows validation error when title is empty", async () => {
    const user = userEvent.setup();
    const item = makeItem();
    render(
      <ItemEditForm
        projectId="VP"
        item={item}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />,
      { wrapper },
    );

    const titleInput = screen.getByLabelText("Title");
    await user.clear(titleInput);
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(screen.getByText("Title is required")).toBeInTheDocument();
    });
  });

  it("calls onCancel when cancel is clicked", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(
      <ItemEditForm
        projectId="VP"
        item={makeItem()}
        onSave={vi.fn()}
        onCancel={onCancel}
      />,
      { wrapper },
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("calls updateItem and onSave on valid submit", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    mockUpdateItem.mockResolvedValueOnce(makeItem({ title: "Changed" }));
    render(
      <ItemEditForm
        projectId="VP"
        item={makeItem()}
        onSave={onSave}
        onCancel={vi.fn()}
      />,
      { wrapper },
    );

    const titleInput = screen.getByLabelText("Title");
    await user.clear(titleInput);
    await user.type(titleInput, "Changed Title");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(mockUpdateItem).toHaveBeenCalledWith("VP", "VP-1", {
        title: "Changed Title",
        description: undefined,
        priority: "normal",
        status: "backlog",
      });
    });
    expect(onSave).toHaveBeenCalledOnce();
  });

  it("reverts changes when cancel is clicked", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    const onCancel = vi.fn();
    render(
      <ItemEditForm
        projectId="VP"
        item={makeItem()}
        onSave={onSave}
        onCancel={onCancel}
      />,
      { wrapper },
    );

    const titleInput = screen.getByLabelText("Title");
    await user.clear(titleInput);
    await user.type(titleInput, "Should be discarded");
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalledOnce();
    expect(onSave).not.toHaveBeenCalled();
    expect(mockUpdateItem).not.toHaveBeenCalled();
  });

  it("does not list 'deleted' as a status option in the dropdown", () => {
    render(
      <ItemEditForm
        projectId="VP"
        item={makeItem()}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />,
      { wrapper },
    );

    const statusSelect = screen.getByLabelText("Status");
    const options = Array.from(
      statusSelect.querySelectorAll("option"),
    ).map((o) => o.value);
    expect(options).not.toContain("deleted");
  });
});
