import { useEffect, useState } from "react";
import styles from "./ThemeSwitcher.module.css";

type Theme = "light" | "dark";

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
      <label className={styles.label} htmlFor="theme-select">
        Theme
      </label>
      <select
        id="theme-select"
        className={styles.select}
        value={theme}
        onChange={(e) => setTheme(e.target.value as Theme)}
        data-test-id="theme-switcher"
      >
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </div>
  );
}
