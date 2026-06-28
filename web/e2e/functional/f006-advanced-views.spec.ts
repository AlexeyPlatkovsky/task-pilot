import { test, expect } from "@playwright/test";
import { openFixtureProject } from "../support/workspace";

test.describe("F006 advanced workspace views", () => {
  test("switches views, filters and sorts the list, and opens a tree item", async ({
    page,
  }) => {
    await openFixtureProject(page);

    await expect(page.getByRole("tab", { name: "Board" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await expect(
      page.locator('[data-item-id="TP-1"]').filter({
        hasText: "Launch advanced workspace",
      }),
    ).toBeVisible();

    await page.getByRole("tab", { name: "List" }).click();
    await expect(page.getByRole("tab", { name: "List" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await expect(page.getByRole("columnheader", { name: /ID/ })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open TP-2" })).toBeVisible();

    await page.getByLabel("List filters").getByLabel("Type").selectOption("bug");
    await expect(page.getByRole("button", { name: "Open TP-3" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open TP-2" })).toBeHidden();

    await page.getByLabel("List filters").getByLabel("Type").selectOption("");
    const firstRow = page.locator("tbody tr").first();
    const sortById = page.getByRole("button", { name: /Sort by ID/ });
    await sortById.evaluate((button) => (button as HTMLButtonElement).click());
    await expect(firstRow).toHaveAttribute("data-item-id", "TP-1");
    await sortById.evaluate((button) => (button as HTMLButtonElement).click());
    await expect(firstRow).toHaveAttribute("data-item-id", "TP-3");

    await page.getByRole("tab", { name: "Tree" }).click();
    await expect(page.getByRole("tab", { name: "Tree" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await page.getByRole("button", { name: "Expand TP-1" }).click();
    await page.getByRole("button", { name: "Expand TP-2" }).click();
    await page
      .getByRole("tree", { name: "Item hierarchy" })
      .getByRole("button", { name: "Open TP-3" })
      .click();

    await expect(
      page.getByRole("dialog", { name: "TP-3: Fix tree regression" }),
    ).toBeVisible();
    await expect(page.getByText("Leaf item opened from the tree view.")).toBeVisible();
  });
});
