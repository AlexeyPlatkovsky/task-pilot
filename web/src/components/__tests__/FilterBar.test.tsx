import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FilterBar } from "../FilterBar";

describe("FilterBar", () => {
  it("renders children inside the filter bar", () => {
    render(
      <FilterBar hasActiveFilters={false} onClear={vi.fn()}>
        <span>Child content</span>
      </FilterBar>,
    );
    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("renders the Clear button", () => {
    render(
      <FilterBar hasActiveFilters={false} onClear={vi.fn()}>
        <span>Filters</span>
      </FilterBar>,
    );
    expect(
      screen.getByRole("button", { name: "Clear filters" }),
    ).toBeInTheDocument();
  });

  it("disables Clear button when no filters are active", () => {
    render(
      <FilterBar hasActiveFilters={false} onClear={vi.fn()}>
        <span>Filters</span>
      </FilterBar>,
    );
    expect(screen.getByRole("button", { name: "Clear filters" })).toBeDisabled();
  });

  it("enables Clear button when filters are active", () => {
    render(
      <FilterBar hasActiveFilters={true} onClear={vi.fn()}>
        <span>Filters</span>
      </FilterBar>,
    );
    expect(
      screen.getByRole("button", { name: "Clear filters" }),
    ).toBeEnabled();
  });

  it("calls onClear when Clear button is clicked", async () => {
    const user = userEvent.setup();
    const onClear = vi.fn();
    render(
      <FilterBar hasActiveFilters={true} onClear={onClear}>
        <span>Filters</span>
      </FilterBar>,
    );
    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("sets aria-label on the filter bar", () => {
    render(
      <FilterBar
        hasActiveFilters={false}
        onClear={vi.fn()}
        ariaLabel="Board filters"
      >
        <span>Filters</span>
      </FilterBar>,
    );
    expect(
      screen.getByLabelText("Board filters"),
    ).toBeInTheDocument();
  });

  it("sets data-test-id on the filter bar", () => {
    render(
      <FilterBar
        hasActiveFilters={false}
        onClear={vi.fn()}
        dataTestId="kanban-board-filters"
      >
        <span>Filters</span>
      </FilterBar>,
    );
    expect(screen.getByTestId("kanban-board-filters")).toBeInTheDocument();
  });
});
