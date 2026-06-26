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

  it("defines all six spacing tokens", () => {
    for (const n of [1, 2, 3, 4, 6, 8]) {
      expect(css, `missing --space-${n}`).toContain(`--space-${n}:`);
    }
  });

  it("defines all four radius tokens", () => {
    for (const size of ["sm", "md", "lg", "xl"]) {
      expect(css, `missing --radius-${size}`).toContain(`--radius-${size}:`);
    }
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

  it("defines both typography tokens", () => {
    for (const name of ["--font-size-sm", "--font-size-base"]) {
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
