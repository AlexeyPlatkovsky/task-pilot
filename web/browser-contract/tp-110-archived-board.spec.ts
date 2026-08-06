/** @file Browser contract tests: Archived list structure and state styling. */

import { test, expect } from "@playwright/test";

test.describe("Archived List Browser Contract", () => {
  async function openArchivedList(page: import("@playwright/test").Page) {
    await page.goto("/");
    const archivedTab = page.locator('[data-test-id="workspace-tab-archived"]');
    await archivedTab.click();
  }

  test("is always available as a non-columnar list", async ({ page }) => {
    await openArchivedList(page);

    await expect(page.locator('[data-test-id="workspace-toggle-archived"]')).toHaveCount(0);
    const list = page.locator('[data-test-id="archived-list"] [aria-label="Archived items"]');
    const row = page.locator('[data-test-id="archived-list-row"][data-item-id="TP-1"]');
    const rowWithDivider = page.locator('[data-test-id="archived-list-row"][data-item-id="TP-2"]');
    const openItem = page.locator('[data-test-id="archived-list-open-TP-1"]');

    await expect(list).toBeVisible();
    await expect(page.locator('[data-test-id^="kanban-column-"]')).toHaveCount(0);
    await expect(row).toContainText("TP-1");
    await expect(row).toContainText("Task");
    await expect(row).toContainText("Done");
    await expect(row).toContainText("Normal");
    await expect(list).toHaveCSS("background-color", "rgb(255, 255, 255)");
    await expect(rowWithDivider).toHaveCSS("border-bottom-color", "rgb(229, 234, 240)");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    await expect(openItem).toBeFocused();
    await expect(openItem).toHaveCSS("outline-color", "rgb(169, 74, 34)");
  });

  test("empty state renders correctly", async ({ page }) => {
    await page.route("**/api/projects/taskpilot-e2e/archived", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: "[]" }),
    );
    await page.goto("/");

    const archivedTab = page.locator('[data-test-id="workspace-tab-archived"]');
    await archivedTab.click();

    // Empty prompt should be visible when no archived items
    await expect(page.locator('[data-test-id="archived-empty-prompt"]')).toBeVisible();
  });

  test("loading state renders spinner", async ({ page }) => {
    await page.route("**/api/projects/taskpilot-e2e/archived", () => new Promise(() => {}));
    await page.goto("/");

    const archivedTab = page.locator('[data-test-id="workspace-tab-archived"]');
    await archivedTab.click();

    await expect(page.getByText("Loading archived items...")).toBeVisible();
  });

  test("error state renders retry button", async ({ page }) => {
    // Simulate API error by intercepting the archived items request
    await page.goto("/");

    // Intercept archived items API call and return error
    await page.route("**/api/projects/*/archived", (route) => {
      route.fulfill({ status: 500, body: "Internal Server Error" });
    });

    const archivedTab = page.locator('[data-test-id="workspace-tab-archived"]');
    await archivedTab.click();

    // Error state should show retry button
    await expect(page.getByRole("button", { name: "Retry" })).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByRole("alert")).toHaveCSS("color", "rgb(220, 53, 69)");
  });
});
