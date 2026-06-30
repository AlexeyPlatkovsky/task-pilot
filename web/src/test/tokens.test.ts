import { describe, it, expect, beforeAll } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

// Verifies tokens.css exists and contains every expected token name (AC-2 partial).
// Dark/light computed-value assertions require a real browser — see Playwright tests.

const TOKENS_PATH = resolve(__dirname, "../tokens.css");
const INDEX_CSS_PATH = resolve(__dirname, "../index.css");
const KANBAN_BOARD_CSS_PATH = resolve(
  __dirname,
  "../components/KanbanBoard.module.css",
);
const KANBAN_COLUMN_CSS_PATH = resolve(
  __dirname,
  "../components/KanbanColumn.module.css",
);
const ROOT_TOKEN_COUNT = 74;

describe("tokens.css — token definitions (AC-2)", () => {
  let css: string;

  beforeAll(() => {
    css = readFileSync(TOKENS_PATH, "utf-8");
  });

  it("defines exactly the approved root token count", () => {
    const rootBlock = css.match(/:root\s*{(?<body>[\s\S]*?)\n}/)?.groups?.body;
    expect(rootBlock, "missing :root token block").toBeDefined();

    const tokenNames = new Set(
      Array.from(rootBlock?.matchAll(/(--[a-z0-9_-]+)\s*:/g) ?? []).map(
        ([, name]) => name,
      ),
    );

    expect(tokenNames.size).toBe(ROOT_TOKEN_COUNT);
  });

  it("defines all six surface tokens", () => {
    for (const name of [
      "--surface-app",
      "--surface-base",
      "--surface-raised",
      "--surface-overlay",
      "--surface-muted",
      "--surface-column",
    ]) {
      expect(css, `missing ${name}`).toContain(`${name}:`);
    }
  });

  it("defines all three border tokens", () => {
    for (const name of [
      "--border-subtle",
      "--border-default",
      "--border-strong",
    ]) {
      expect(css, `missing ${name}`).toContain(`${name}:`);
    }
  });

  it("defines all five text tokens", () => {
    for (const name of [
      "--text-primary",
      "--text-secondary",
      "--text-muted",
      "--text-disabled",
      "--text-inverse",
    ]) {
      expect(css, `missing ${name}`).toContain(`${name}:`);
    }
  });

  it("defines all five accent tokens", () => {
    for (const name of [
      "--brand-accent",
      "--accent",
      "--accent-hover",
      "--accent-fg",
      "--accent-subtle",
    ]) {
      expect(css, `missing ${name}`).toContain(`${name}:`);
    }
  });

  it("defines bg and fg tokens for all six statuses", () => {
    const statuses = [
      "backlog",
      "ready",
      "inprogress",
      "done",
      "cancelled",
      "deleted",
    ];
    for (const status of statuses) {
      expect(css, `missing --status-${status}-bg`).toContain(
        `--status-${status}-bg:`,
      );
      expect(css, `missing --status-${status}-fg`).toContain(
        `--status-${status}-fg:`,
      );
    }
  });

  it("defines bg and fg tokens for all three priorities", () => {
    for (const priority of ["low", "normal", "high"]) {
      expect(css, `missing --priority-${priority}-bg`).toContain(
        `--priority-${priority}-bg:`,
      );
      expect(css, `missing --priority-${priority}-fg`).toContain(
        `--priority-${priority}-fg:`,
      );
    }
  });

  it("defines all six feedback tokens", () => {
    for (const name of [
      "--feedback-error",
      "--feedback-error-bg",
      "--feedback-warning",
      "--feedback-warning-bg",
      "--feedback-success",
      "--feedback-success-bg",
    ]) {
      expect(css, `missing ${name}`).toContain(`${name}:`);
    }
  });

  it("defines all seven spacing tokens", () => {
    for (const n of ["1", "1_5", "2", "3", "4", "6", "8"]) {
      expect(css, `missing --space-${n}`).toContain(`--space-${n}:`);
    }
  });

  it("defines the Agent Manifesto radius tokens with correct values", () => {
    expect(css).toContain("--radius-sm: 10px");
    expect(css).toContain("--radius-md: 16px");
    expect(css).toContain("--radius-lg: 20px");
    expect(css).toContain("--radius-pill: 999px");
  });

  it("no longer defines --radius-xl after the radius merge", () => {
    expect(css).not.toContain("--radius-xl");
  });

  it("defines all three shadow tokens", () => {
    for (const name of [
      "--shadow-card",
      "--shadow-card-hover",
      "--shadow-modal",
    ]) {
      expect(css, `missing ${name}`).toContain(`${name}:`);
    }
  });

  it("defines the full typography token set", () => {
    for (const name of [
      "--font-family-base",
      "--font-size-xs",
      "--font-size-sm",
      "--font-size-base",
      "--font-size-lg",
      "--font-weight-normal",
      "--font-weight-semibold",
      "--line-height-tight",
      "--line-height-base",
      "--line-height-relaxed",
      "--letter-spacing-wide",
    ]) {
      expect(css, `missing ${name}`).toContain(`${name}:`);
    }
  });

  it("defines desktop layout tokens for the local-only workspace", () => {
    expect(css).toContain("--viewport-min-width: 1280px");
    expect(css).toContain("--content-width-comfortable: 1440px");
    expect(css).toContain("--content-max-width: 1760px");
    expect(css).toContain("--kanban-column-min: 248px");
    expect(css).toContain("--kanban-column-max: 320px");
  });

  it("applies active desktop layout tokens to the app shell and Kanban board", () => {
    const indexCss = readFileSync(INDEX_CSS_PATH, "utf-8");
    const boardCss = readFileSync(KANBAN_BOARD_CSS_PATH, "utf-8");
    const columnCss = readFileSync(KANBAN_COLUMN_CSS_PATH, "utf-8");

    expect(indexCss).toContain("min-width: var(--viewport-min-width)");
    expect(boardCss).toContain("max-width: var(--content-max-width)");
    expect(columnCss).toContain("flex: 1 1 var(--kanban-column-min)");
    expect(columnCss).toContain("min-width: var(--kanban-column-min)");
    expect(columnCss).not.toContain("max-width: var(--kanban-column-max)");
    expect(columnCss).toContain("padding-inline-start: var(--space-2)");
  });

  it("includes a dark theme via prefers-color-scheme media query", () => {
    expect(css).toContain("prefers-color-scheme: dark");
  });

  it("includes explicit data-theme=dark override block", () => {
    expect(css).toContain('[data-theme="dark"]');
  });

  it("includes explicit data-theme=light override block", () => {
    expect(css).toContain('[data-theme="light"]');
  });
});
