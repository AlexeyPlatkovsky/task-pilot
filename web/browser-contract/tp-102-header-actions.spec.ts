/** @file Browser contract tests: header theme toggle and icon actions styling (spec 0010). */

import { test, expect } from "@playwright/test";

const option = (value: string) => `[data-test-id="theme-option-${value}"]`;
const doctorButton = '[data-test-id="header-doctor-button"]';
const unregisterButton = '[data-test-id="header-unregister-button"]';

test.describe("Header actions browser contract", () => {
  test.beforeEach(async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto("/");
    await page.evaluate(() => window.localStorage.clear());
    await page.reload();
    await expect(page.locator(doctorButton)).toBeVisible();
  });

  test("checked theme option uses accent-subtle background and accent icon in light", async ({
    page,
  }) => {
    const checked = page.locator(option("auto"));
    await expect(checked).toHaveAttribute("aria-checked", "true");
    await expect(checked).toHaveCSS("background-color", "rgb(246, 214, 198)");
    await expect(checked).toHaveCSS("color", "rgb(169, 74, 34)");
    await expect(page.locator(option("dark"))).toHaveCSS(
      "background-color",
      "rgba(0, 0, 0, 0)",
    );
  });

  test("checked theme option follows dark tokens after selecting dark", async ({
    page,
  }) => {
    await page.locator(option("dark")).click();
    await page.mouse.move(0, 0);
    const checked = page.locator(option("dark"));
    await expect(checked).toHaveCSS("background-color", "rgb(58, 29, 18)");
    await expect(checked).toHaveCSS("color", "rgb(224, 138, 93)");
  });

  test("keyboard focus shows the shared accent outline on icon buttons and theme options", async ({
    page,
  }) => {
    await page.locator(doctorButton).focus();
    await page.keyboard.press("Tab");
    const unregister = page.locator(unregisterButton);
    await expect(unregister).toBeFocused();
    await expect(unregister).toHaveCSS("outline-style", "solid");
    await expect(unregister).toHaveCSS("outline-color", "rgb(169, 74, 34)");

    await page.keyboard.press("Tab");
    const auto = page.locator(option("auto"));
    await expect(auto).toBeFocused();
    await expect(auto).toHaveCSS("outline-style", "solid");
    await expect(auto).toHaveCSS("outline-color", "rgb(169, 74, 34)");
  });

  test("unregister icon signals destructive effect on hover", async ({ page }) => {
    await page.locator(unregisterButton).hover();
    await expect(page.locator(unregisterButton)).toHaveCSS(
      "color",
      "rgb(220, 53, 69)",
    );
  });
});
