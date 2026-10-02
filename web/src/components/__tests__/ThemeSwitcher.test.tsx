import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeSwitcher } from "../ThemeSwitcher";
import { THEME_STORAGE_KEY } from "../../theme";

const OPTIONS = [
  ["auto", "Auto theme"],
  ["light", "Light theme"],
  ["dark", "Dark theme"],
] as const;

function resetTheme() {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
}

describe("ThemeSwitcher", () => {
  beforeEach(resetTheme);
  afterEach(resetTheme);

  it("stores the theme under the taskpilot.theme key", () => {
    expect(THEME_STORAGE_KEY).toBe("taskpilot.theme");
  });

  it("renders a Theme radiogroup with auto, light, dark in order and tooltips", () => {
    render(<ThemeSwitcher />);

    const group = screen.getByRole("radiogroup", { name: "Theme" });
    expect(group).toHaveAttribute("data-test-id", "theme-switcher");
    const radios = screen.getAllByRole("radio");
    expect(radios).toHaveLength(3);
    OPTIONS.forEach(([value, label], index) => {
      expect(radios[index]).toBe(screen.getByRole("radio", { name: label }));
      expect(radios[index]).toHaveAttribute("title", label);
      expect(radios[index]).toHaveAttribute("data-test-id", `theme-option-${value}`);
    });
  });

  it("defaults to auto with no data-theme when nothing is stored", () => {
    render(<ThemeSwitcher />);

    expect(screen.getByRole("radio", { name: "Auto theme" })).toBeChecked();
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });

  it.each(OPTIONS)(
    "selecting %s checks only that option and persists it",
    async (value, label) => {
      const user = userEvent.setup();
      if (value === "auto") {
        window.localStorage.setItem(THEME_STORAGE_KEY, "dark");
        document.documentElement.setAttribute("data-theme", "dark");
      }
      render(<ThemeSwitcher />);

      await user.click(screen.getByRole("radio", { name: label }));

      for (const [, other] of OPTIONS) {
        const radio = screen.getByRole("radio", { name: other });
        if (other === label) expect(radio).toBeChecked();
        else expect(radio).not.toBeChecked();
      }
      expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe(value);
      if (value === "auto") {
        expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
      } else {
        expect(document.documentElement.getAttribute("data-theme")).toBe(value);
      }
    },
  );

  it("restores a stored theme on mount", () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, "dark");
    render(<ThemeSwitcher />);

    expect(screen.getByRole("radio", { name: "Dark theme" })).toBeChecked();
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("falls back to auto for an unknown stored value", () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, "purple");
    render(<ThemeSwitcher />);

    expect(screen.getByRole("radio", { name: "Auto theme" })).toBeChecked();
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });

  it("uses a roving tabindex and arrow keys move and select with wrap", async () => {
    const user = userEvent.setup();
    render(<ThemeSwitcher />);

    const auto = screen.getByRole("radio", { name: "Auto theme" });
    expect(auto).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("radio", { name: "Dark theme" })).toHaveAttribute(
      "tabindex",
      "-1",
    );

    auto.focus();
    await user.keyboard("{ArrowRight}");
    const light = screen.getByRole("radio", { name: "Light theme" });
    expect(light).toBeChecked();
    expect(light).toHaveFocus();

    await user.keyboard("{ArrowLeft}{ArrowLeft}");
    const dark = screen.getByRole("radio", { name: "Dark theme" });
    expect(dark).toBeChecked();
    expect(dark).toHaveFocus();
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("supports Up/Down arrows and Space/Enter selection", async () => {
    const user = userEvent.setup();
    render(<ThemeSwitcher />);

    screen.getByRole("radio", { name: "Auto theme" }).focus();
    await user.keyboard("{ArrowDown}");
    expect(screen.getByRole("radio", { name: "Light theme" })).toBeChecked();
    await user.keyboard("{ArrowUp}");
    expect(screen.getByRole("radio", { name: "Auto theme" })).toBeChecked();

    // Space/Enter select the focused option even if focus moved without selection.
    const dark = screen.getByRole("radio", { name: "Dark theme" });
    dark.focus();
    await user.keyboard(" ");
    expect(dark).toBeChecked();
    const light = screen.getByRole("radio", { name: "Light theme" });
    light.focus();
    await user.keyboard("{Enter}");
    expect(light).toBeChecked();
  });

  it("falls back to auto when reading localStorage throws", () => {
    const original = Storage.prototype.getItem;
    Storage.prototype.getItem = () => {
      throw new Error("blocked");
    };
    try {
      render(<ThemeSwitcher />);
      expect(screen.getByRole("radio", { name: "Auto theme" })).toBeChecked();
    } finally {
      Storage.prototype.getItem = original;
    }
  });

  it("keeps working when localStorage throws", async () => {
    const user = userEvent.setup();
    const original = Storage.prototype.setItem;
    Storage.prototype.setItem = () => {
      throw new Error("blocked");
    };
    try {
      render(<ThemeSwitcher />);
      await user.click(screen.getByRole("radio", { name: "Dark theme" }));
      expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    } finally {
      Storage.prototype.setItem = original;
    }
  });
});

describe("index.html theme bootstrap", () => {
  beforeEach(resetTheme);
  afterEach(resetTheme);

  const html = readFileSync(resolve(__dirname, "../../../index.html"), "utf8");

  function runBootstrap() {
    const match = html.match(
      /<script data-theme-bootstrap>([\s\S]*?)<\/script>/,
    );
    expect(match, "index.html must contain the theme bootstrap script").not.toBeNull();
    new Function(match![1])();
  }

  it("runs in <head> before the app module script", () => {
    const head = html.slice(0, html.indexOf("</head>"));
    expect(head).toContain("<script data-theme-bootstrap>");
    expect(html.indexOf("data-theme-bootstrap")).toBeLessThan(
      html.indexOf('src="/src/main.tsx"'),
    );
  });

  it("does not throw when localStorage reads fail", () => {
    const original = Storage.prototype.getItem;
    Storage.prototype.getItem = () => {
      throw new Error("blocked");
    };
    try {
      expect(() => runBootstrap()).not.toThrow();
      expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
    } finally {
      Storage.prototype.getItem = original;
    }
  });

  it.each(["light", "dark"])("applies stored %s before mount", (value) => {
    window.localStorage.setItem("taskpilot.theme", value);
    runBootstrap();
    expect(document.documentElement.getAttribute("data-theme")).toBe(value);
  });

  it.each([null, "auto", "purple"])(
    "leaves data-theme unset for stored %s",
    (value) => {
      if (value !== null) window.localStorage.setItem("taskpilot.theme", value);
      runBootstrap();
      expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
    },
  );
});
