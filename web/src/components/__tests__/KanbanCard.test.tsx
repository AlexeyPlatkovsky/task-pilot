import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { KanbanCard } from "../KanbanCard";
import type { ItemSummary, ItemType } from "../../types";

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

describe("KanbanCard", () => {
  it("renders item id and title", () => {
    render(<KanbanCard item={makeItem()} />);
    expect(screen.getByText("VP-1")).toBeInTheDocument();
    expect(screen.getByText("Test Item")).toBeInTheDocument();
  });

  it("has aria-label for accessibility", () => {
    render(<KanbanCard item={makeItem()} onClick={() => {}} />);
    const card = screen.getByLabelText("VP-1: Test Item");
    expect(card).toBeInTheDocument();
    expect(card.tagName).toBe("DIV");
  });

  it("shows invalid badge for invalid items", () => {
    const { container } = render(
      <KanbanCard item={makeItem({ valid: false })} />,
    );
    expect(container.querySelector(".invalidBadge")).not.toBeNull();
  });

  // AC-9: each item type must render an SVG icon with aria-label, not a Unicode glyph
  const typeIconCases: Array<[ItemType, string]> = [
    ["epic", "epic"],
    ["feature", "feature"],
    ["task", "task"],
    ["bug", "bug"],
  ];

  it.each(typeIconCases)(
    "renders an SVG icon with aria-label='%s' for type %s",
    (type, expectedLabel) => {
      const { container } = render(<KanbanCard item={makeItem({ type })} />);
      const svg = container.querySelector(`svg[aria-label="${expectedLabel}"]`);
      expect(svg).not.toBeNull();
    },
  );

  it("does not render Unicode glyph characters as text content for any type icon", () => {
    const unicodeGlyphs = ["⬛", "▶", "□", "⚠"];
    const types: ItemType[] = ["epic", "feature", "task", "bug"];
    for (const type of types) {
      const { container, unmount } = render(
        <KanbanCard item={makeItem({ type })} />,
      );
      const text = container.textContent ?? "";
      for (const glyph of unicodeGlyphs) {
        expect(text, `type ${type} should not render glyph ${glyph}`).not.toContain(
          glyph,
        );
      }
      unmount();
    }
  });
});
