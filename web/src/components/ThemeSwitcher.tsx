import { useEffect, useState } from "react";
import { DropdownSelect, type DropdownOption } from "./DropdownSelect";
import styles from "./ThemeSwitcher.module.css";

type Theme = "light" | "dark";

const THEME_OPTIONS: DropdownOption<Theme>[] = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
];

function getSystemTheme(): Theme {
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

function getStoredTheme(): Theme | null {
  const attr = document.documentElement.getAttribute("data-theme");
  if (attr === "light" || attr === "dark") return attr;
  return null;
}

function applyTheme(theme: Theme | null) {
  if (theme === null) {
    document.documentElement.removeAttribute("data-theme");
  } else {
    document.documentElement.setAttribute("data-theme", theme);
  }
}

export function ThemeSwitcher() {
  const [theme, setTheme] = useState<Theme>(() => {
    return getStoredTheme() ?? getSystemTheme();
  });

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  return (
    <div className={styles.switcher}>
      <DropdownSelect
        id="theme-select"
        label="Theme"
        value={theme}
        options={THEME_OPTIONS}
        onChange={setTheme}
        size="theme"
        dataTestId="theme-switcher"
      />
    </div>
  );
}
