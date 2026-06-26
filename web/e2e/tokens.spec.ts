import { test, expect } from "@playwright/test";

const APP_URL = "http://localhost:3000";

test.describe("Design token themes (AC-3, AC-4, AC-5)", () => {
  test("AC-3: light defaults resolve via :root", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto(APP_URL);

    const tokens = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement);
      return {
        surfaceApp: style.getPropertyValue("--surface-app").trim(),
        surfaceBase: style.getPropertyValue("--surface-base").trim(),
        textPrimary: style.getPropertyValue("--text-primary").trim(),
      };
    });

    expect(tokens.surfaceApp).toBe("#f5f5f5");
    expect(tokens.surfaceBase).toBe("#ffffff");
    expect(tokens.textPrimary).toBe("#1a1a1a");
  });

  test("AC-4: data-theme=dark overrides apply dark tokens", async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto(APP_URL);
    await page.evaluate(() =>
      document.documentElement.setAttribute("data-theme", "dark"),
    );

    const tokens = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement);
      return {
        surfaceApp: style.getPropertyValue("--surface-app").trim(),
        surfaceBase: style.getPropertyValue("--surface-base").trim(),
        textPrimary: style.getPropertyValue("--text-primary").trim(),
      };
    });

    expect(tokens.surfaceApp).toBe("#111113");
    expect(tokens.surfaceBase).toBe("#1c1c1e");
    expect(tokens.textPrimary).toBe("#f5f5f7");
  });

  test("AC-5: data-theme=light overrides when OS prefers dark", async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto(APP_URL);
    await page.evaluate(() =>
      document.documentElement.setAttribute("data-theme", "light"),
    );

    const tokens = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement);
      return {
        surfaceApp: style.getPropertyValue("--surface-app").trim(),
        surfaceBase: style.getPropertyValue("--surface-base").trim(),
        textPrimary: style.getPropertyValue("--text-primary").trim(),
        // These two are set to #1a1a1a by the dark @media block;
        // [data-theme="light"] must explicitly reset them to light values.
        accentFg: style.getPropertyValue("--accent-fg").trim(),
        statusInprogressFg: style
          .getPropertyValue("--status-inprogress-fg")
          .trim(),
      };
    });

    expect(tokens.surfaceApp).toBe("#f5f5f5");
    expect(tokens.surfaceBase).toBe("#ffffff");
    expect(tokens.textPrimary).toBe("#1a1a1a");
    expect(tokens.accentFg).toBe("#ffffff");
    expect(tokens.statusInprogressFg).toBe("#ffffff");
  });

  test("OS dark preference activates dark tokens automatically", async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto(APP_URL);

    const tokens = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement);
      return {
        surfaceApp: style.getPropertyValue("--surface-app").trim(),
        textPrimary: style.getPropertyValue("--text-primary").trim(),
      };
    });

    expect(tokens.surfaceApp).toBe("#111113");
    expect(tokens.textPrimary).toBe("#f5f5f7");
  });
});
