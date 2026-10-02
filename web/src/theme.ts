export type ThemeChoice = "auto" | "light" | "dark";

export const THEME_STORAGE_KEY = "taskpilot.theme";

export const THEME_CHOICES: readonly ThemeChoice[] = ["auto", "light", "dark"];

function isThemeChoice(value: unknown): value is ThemeChoice {
  return value === "auto" || value === "light" || value === "dark";
}

/** Read the stored choice; missing, unknown, or unreadable values mean "auto". */
export function readStoredTheme(): ThemeChoice {
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
    return isThemeChoice(stored) ? stored : "auto";
  } catch {
    return "auto";
  }
}

export function storeTheme(theme: ThemeChoice): void {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Storage may be blocked; the choice still applies for this page view.
  }
}

/** "auto" removes data-theme so prefers-color-scheme decides, including live OS changes. */
export function applyTheme(theme: ThemeChoice): void {
  if (theme === "auto") {
    document.documentElement.removeAttribute("data-theme");
  } else {
    document.documentElement.setAttribute("data-theme", theme);
  }
}
