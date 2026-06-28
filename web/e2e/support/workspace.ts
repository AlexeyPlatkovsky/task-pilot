import { expect, type Page } from "@playwright/test";

export const fixtureProject = {
  id: "taskpilot-e2e",
  key: "TP",
  name: "TaskPilot E2E",
} as const;

export async function openFixtureProject(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "TaskPilot" })).toBeVisible();
  await page.getByRole("combobox").selectOption(fixtureProject.id);
  await expect(page.getByText("All items valid")).toBeVisible();
}

export function kanbanColumn(page: Page, status: string) {
  return page.locator(`[data-status="${status}"]`);
}

export function kanbanCard(page: Page, itemId: string) {
  return page.locator(`[data-item-id="${itemId}"]`);
}

export async function expectCardInColumn(
  page: Page,
  itemId: string,
  status: string,
) {
  await expect(kanbanColumn(page, status).locator(`[data-item-id="${itemId}"]`))
    .toBeVisible();
}
