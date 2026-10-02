import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Monitor, Moon, Sun, type LucideIcon } from "lucide-react";
import {
  THEME_CHOICES,
  applyTheme,
  readStoredTheme,
  storeTheme,
  type ThemeChoice,
} from "../theme";
import styles from "./ThemeSwitcher.module.css";

const OPTIONS: Record<ThemeChoice, { label: string; icon: LucideIcon }> = {
  auto: { label: "Auto theme", icon: Monitor },
  light: { label: "Light theme", icon: Sun },
  dark: { label: "Dark theme", icon: Moon },
};

const NEXT_KEYS = new Set(["ArrowRight", "ArrowDown"]);
const PREV_KEYS = new Set(["ArrowLeft", "ArrowUp"]);

export function ThemeSwitcher() {
  const [theme, setTheme] = useState<ThemeChoice>(readStoredTheme);
  const buttons = useRef<Partial<Record<ThemeChoice, HTMLButtonElement | null>>>(
    {},
  );

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  function select(next: ThemeChoice, focus = false) {
    setTheme(next);
    storeTheme(next);
    if (focus) buttons.current[next]?.focus();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, current: ThemeChoice) {
    const step = NEXT_KEYS.has(event.key) ? 1 : PREV_KEYS.has(event.key) ? -1 : 0;
    if (step === 0) return;
    event.preventDefault();
    const index = THEME_CHOICES.indexOf(current);
    const next = THEME_CHOICES[(index + step + THEME_CHOICES.length) % THEME_CHOICES.length];
    if (next) select(next, true);
  }

  return (
    <div
      className={styles.switcher}
      role="radiogroup"
      aria-label="Theme"
      data-test-id="theme-switcher"
    >
      {THEME_CHOICES.map((choice) => {
        const { label, icon: Icon } = OPTIONS[choice];
        const checked = choice === theme;
        return (
          <button
            key={choice}
            ref={(el) => {
              buttons.current[choice] = el;
            }}
            type="button"
            role="radio"
            aria-checked={checked}
            aria-label={label}
            title={label}
            tabIndex={checked ? 0 : -1}
            className={styles.option}
            data-test-id={`theme-option-${choice}`}
            onClick={() => select(choice)}
            onKeyDown={(event) => handleKeyDown(event, choice)}
          >
            <Icon size={16} aria-hidden="true" />
          </button>
        );
      })}
    </div>
  );
}
