import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeSwitcher } from "../ThemeSwitcher";

describe("ThemeSwitcher", () => {
  it("renders the theme label and select", () => {
    render(<ThemeSwitcher />);

    expect(screen.getByLabelText("Theme")).toBeInTheDocument();
    expect(screen.getByTestId("theme-switcher")).toBeInTheDocument();
  });

  it("has Light and Dark options", () => {
    render(<ThemeSwitcher />);

    const select = screen.getByTestId("theme-switcher") as HTMLSelectElement;
    expect(select.options.length).toBe(2);
    expect(select.options[0].value).toBe("light");
    expect(select.options[0].text).toBe("Light");
    expect(select.options[1].value).toBe("dark");
    expect(select.options[1].text).toBe("Dark");
  });

  it("sets data-theme on the document element when changed to dark", async () => {
    const user = userEvent.setup();
    document.documentElement.removeAttribute("data-theme");

    render(<ThemeSwitcher />);

    const select = screen.getByTestId("theme-switcher");
    await user.selectOptions(select, "dark");

    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("sets data-theme on the document element when changed to light", async () => {
    const user = userEvent.setup();
    document.documentElement.setAttribute("data-theme", "dark");

    render(<ThemeSwitcher />);

    const select = screen.getByTestId("theme-switcher");
    await user.selectOptions(select, "light");

    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });
});
