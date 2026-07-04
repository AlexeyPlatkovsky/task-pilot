import { expect, test, type Page, type Route } from "@playwright/test";

const project = {
  id: "taskpilot-e2e",
  key: "TP",
  name: "TaskPilot E2E",
  active: true,
};

const longItemId = "TP-12345678901234567890";

const itemSummary = {
  id: longItemId,
  title: "Long identity layout check",
  type: "feature",
  status: "ready",
  priority: "high",
  valid: true,
  findings: [],
};

const itemDetail = {
  schema_version: 1,
  ...itemSummary,
  created_at: "2026-06-28T10:09:00Z",
  updated_at: "2026-06-28T10:10:00Z",
  description: "Browser layout contract fixture.",
  comments: [],
};

test("item modal header and summary do not overlap at desktop minimum width", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await mockProjectApi(page);

  await page.goto("/");
  await page.locator('[data-test-id="project-selector"]').click();
  await page.getByRole("option", { name: "TaskPilot E2E (TP)" }).click();
  await page.locator(`[data-test-id="kanban-card-${longItemId}"]`).click();

  const modal = page.locator(`[data-test-id="item-modal-${longItemId}"]`);
  await expect(modal).toBeVisible();
  await expect(modal.locator('[data-test-id="item-modal-type"]')).toHaveText("FEAT");

  const actionBox = await requiredBox(
    modal.locator('[data-test-id="item-modal-actions"]'),
  );
  for (const testId of [
    "item-modal-type",
    "item-modal-id",
    "item-modal-item-title",
  ]) {
    const box = await requiredBox(modal.locator(`[data-test-id="${testId}"]`));
    expect(box.x + box.width).toBeLessThanOrEqual(actionBox.x);
  }

  const summaryBox = await requiredBox(modal.getByLabel("Item summary"));
  const infoBox = await requiredBox(modal.getByRole("heading", { name: "Info" }));
  expect(summaryBox.y + summaryBox.height).toBeLessThanOrEqual(infoBox.y);
});

async function mockProjectApi(page: Page) {
  await page.route("**/api/projects", (route) => fulfillJson(route, [project]));
  await page.route("**/api/projects/taskpilot-e2e/validate", (route) =>
    fulfillJson(route, {
      ok: true,
      summary: { errors: 0, warnings: 0 },
      findings: [],
    }),
  );
  await page.route("**/api/projects/taskpilot-e2e/items", (route) =>
    fulfillJson(route, [itemSummary]),
  );
  await page.route(`**/api/projects/taskpilot-e2e/items/${longItemId}`, (route) =>
    fulfillJson(route, itemDetail),
  );
}

async function fulfillJson(route: Route, body: unknown) {
  await route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function requiredBox(locator: ReturnType<Page["locator"]>) {
  const box = await locator.boundingBox();
  expect(box).not.toBeNull();
  return box!;
}
