import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeSwitcher } from "../ThemeSwitcher";

describe("ThemeSwitcher", () => {
  it("renders the theme label and dropdown trigger", () => {
    render(<ThemeSwitcher />);

    expect(
      screen.getByRole("button", { name: "Theme: Light" }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("theme-switcher")).toBeInTheDocument();
  });

  it("renders theme options in the shared dropdown style", async () => {
    const user = userEvent.setup();
    render(<ThemeSwitcher />);

    await user.click(screen.getByRole("button", { name: "Theme: Light" }));

    const menu = screen.getByRole("listbox", { name: "Theme options" });
    expect(menu).toHaveAttribute("data-placement", "below");
    expect(screen.getByRole("option", { name: "Light" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("option", { name: "Dark" })).toBeInTheDocument();
  });

  it("sets data-theme on the document element when changed to dark", async () => {
    const user = userEvent.setup();
    document.documentElement.removeAttribute("data-theme");

    render(<ThemeSwitcher />);

    await user.click(screen.getByRole("button", { name: "Theme: Light" }));
    await user.click(screen.getByRole("option", { name: "Dark" }));

    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("sets data-theme on the document element when changed to light", async () => {
    const user = userEvent.setup();
    document.documentElement.setAttribute("data-theme", "dark");

    render(<ThemeSwitcher />);

    await user.click(screen.getByRole("button", { name: "Theme: Dark" }));
    await user.click(screen.getByRole("option", { name: "Light" }));

    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });
});
