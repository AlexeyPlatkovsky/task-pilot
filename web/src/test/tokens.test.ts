import { describe, it, expect, beforeAll } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

// Verifies tokens.css exists and contains every expected token name (AC-2 partial).
// Dark/light computed-value assertions require a real browser — see Playwright tests.

const TOKENS_PATH = resolve(__dirname, "../tokens.css");

describe("tokens.css — token definitions (AC-2)", () => {
  let css: string;

  beforeAll(() => {
    css = readFileSync(TOKENS_PATH, "utf-8");
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

  it("defines all four accent tokens", () => {
    for (const name of [
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

  it("defines all four feedback tokens", () => {
    for (const name of [
      "--feedback-error",
      "--feedback-error-bg",
      "--feedback-warning",
      "--feedback-warning-bg",
    ]) {
      expect(css, `missing ${name}`).toContain(`${name}:`);
    }
  });

  it("defines all seven spacing tokens", () => {
    for (const n of ["1", "1_5", "2", "3", "4", "6", "8"]) {
      expect(css, `missing --space-${n}`).toContain(`--space-${n}:`);
    }
  });

  it("defines the three merged radius tokens with correct values", () => {
    expect(css).toContain("--radius-sm: 4px");
    expect(css).toContain("--radius-md: 6px");
    expect(css).toContain("--radius-lg: 8px");
  });

  it("no longer defines --radius-xl after the radius merge (F009-R10)", () => {
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

  it("defines the full typography token set (F009-R10)", () => {
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
