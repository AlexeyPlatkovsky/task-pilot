import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DndContext } from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { SortableKanbanCard } from "../SortableKanbanCard";
import type { ItemSummary } from "../../types";

function makeItem(overrides: Partial<ItemSummary> = {}): ItemSummary {
  return {
    id: "VP-1",
    title: "Test Item",
    type: "task",
    status: "backlog",
    priority: "normal",
    valid: true,
    ...overrides,
  };
}

function Wrapper({
  itemIds,
  children,
}: {
  itemIds: string[];
  children: React.ReactNode;
}) {
  return (
    <DndContext>
      <SortableContext items={itemIds} strategy={verticalListSortingStrategy}>
        {children}
      </SortableContext>
    </DndContext>
  );
}

describe("SortableKanbanCard", () => {
  it("renders KanbanCard for a valid item", () => {
    const item = makeItem();
    render(
      <Wrapper itemIds={[item.id]}>
        <SortableKanbanCard item={item} />
      </Wrapper>,
    );

    expect(screen.getByText("VP-1")).toBeInTheDocument();
    expect(screen.getByText("Test Item")).toBeInTheDocument();
  });

  it("renders KanbanCard for an invalid item", () => {
    const item = makeItem({ valid: false });
    render(
      <Wrapper itemIds={[item.id]}>
        <SortableKanbanCard item={item} />
      </Wrapper>,
    );

    expect(screen.getByText("VP-1")).toBeInTheDocument();
  });

  it("disables touch-action on the wrapper", () => {
    const item = makeItem();
    const { container } = render(
      <Wrapper itemIds={[item.id]}>
        <SortableKanbanCard item={item} />
      </Wrapper>,
    );

    const wrapper = container.querySelector("[class*='wrapper']");
    expect(wrapper).not.toBeNull();
  });

  it("does not render a ghost card with reduced opacity when not dragging", () => {
    const item = makeItem();
    const { container } = render(
      <Wrapper itemIds={[item.id]}>
        <SortableKanbanCard item={item} />
      </Wrapper>,
    );

    const wrapper = container.querySelector("[class*='wrapper']");
    expect(wrapper).not.toBeNull();
    const styleAttr = wrapper!.getAttribute("style") ?? "";
    expect(styleAttr).not.toContain("opacity: 0.5");
  });

  it("renders with full opacity when not dragging", () => {
    const item = makeItem();
    const { container } = render(
      <Wrapper itemIds={[item.id]}>
        <SortableKanbanCard item={item} />
      </Wrapper>,
    );

    const wrapper = container.querySelector("[class*='wrapper']");
    expect(wrapper).not.toBeNull();
    const styleAttr = wrapper!.getAttribute("style") ?? "";
    expect(styleAttr).toContain("opacity: 1");
  });

  it("creates a sortable wrapper with button role for valid items", () => {
    const item = makeItem();
    render(
      <Wrapper itemIds={[item.id]}>
        <SortableKanbanCard item={item} onClick={() => {}} />
      </Wrapper>,
    );

    const buttons = screen.getAllByRole("button");
    const cardButton = buttons.find((b) =>
      b.getAttribute("aria-roledescription") === "sortable",
    );
    expect(cardButton).not.toBeUndefined();
    expect(cardButton!.getAttribute("aria-disabled")).toBe("false");
  });

  it("disables sortable wrapper for invalid items", () => {
    const item = makeItem({ valid: false });
    render(
      <Wrapper itemIds={[item.id]}>
        <SortableKanbanCard item={item} />
      </Wrapper>,
    );

    const buttons = screen.getAllByRole("button");
    const cardButton = buttons.find((b) =>
      b.getAttribute("aria-roledescription") === "sortable",
    );
    expect(cardButton).not.toBeUndefined();
    expect(cardButton!.getAttribute("aria-disabled")).toBe("true");
  });

  it("keeps opacity 0 and no transition when item.id matches droppedItemId", () => {
    const item = makeItem();
    const { container } = render(
      <Wrapper itemIds={[item.id]}>
        <SortableKanbanCard item={item} droppedItemId={item.id} />
      </Wrapper>,
    );

    const wrapper = container.querySelector("[class*='wrapper']");
    expect(wrapper).not.toBeNull();
    const styleAttr = wrapper!.getAttribute("style") ?? "";
    expect(styleAttr).toContain("opacity: 0");
    expect(styleAttr).not.toContain("transition:");
  });

  it("keeps opacity 1 when droppedItemId is a different item", () => {
    const item = makeItem();
    const { container } = render(
      <Wrapper itemIds={[item.id]}>
        <SortableKanbanCard item={item} droppedItemId="VP-99" />
      </Wrapper>,
    );

    const wrapper = container.querySelector("[class*='wrapper']");
    expect(wrapper).not.toBeNull();
    const styleAttr = wrapper!.getAttribute("style") ?? "";
    expect(styleAttr).toContain("opacity: 1");
  });

  it("keeps opacity 0 and no transition when item.id matches activeDraggedItemId", () => {
    const item = makeItem();
    const { container } = render(
      <Wrapper itemIds={[item.id]}>
        <SortableKanbanCard item={item} activeDraggedItemId={item.id} />
      </Wrapper>,
    );

    const wrapper = container.querySelector("[class*='wrapper']");
    expect(wrapper).not.toBeNull();
    const styleAttr = wrapper!.getAttribute("style") ?? "";
    expect(styleAttr).toContain("opacity: 0");
    expect(styleAttr).not.toContain("transition:");
  });
});
