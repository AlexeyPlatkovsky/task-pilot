import { expect, test, type Page } from "@playwright/test";

const project = {
  id: "taskpilot-layout",
  key: "TL",
  name: "TaskPilot Layout",
  active: true,
};

const items = [
  {
    id: "TL-1",
    title: "Short title",
    type: "task",
    status: "backlog",
    priority: "normal",
    valid: true,
    findings: [],
  },
  {
    id: "TL-2",
    title: "This title is long enough to wrap across exactly two visible lines",
    type: "task",
    status: "backlog",
    priority: "normal",
    valid: true,
    findings: [],
  },
  {
    id: "TL-3",
    title:
      "This title is deliberately much longer than two visible lines so Chromium must clamp the text while preserving the same card height",
    type: "task",
    status: "backlog",
    priority: "normal",
    valid: true,
    findings: [],
  },
] as const;

async function mockLayoutProject(page: Page) {
  await page.route("**/api/projects", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([project]),
    }),
  );
  await page.route("**/api/projects/taskpilot-layout/validate", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        summary: { errors: 0, warnings: 0 },
        findings: [],
      }),
    }),
  );
  await page.route("**/api/projects/taskpilot-layout/items", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(items),
    }),
  );
}

test.describe("Kanban card layout", () => {
  test("card titles reserve two visible lines and keep cards the same height", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await mockLayoutProject(page);

    await page.goto("/");
    await page
      .locator('[data-test-id="project-selector"]')
      .selectOption({ label: "TaskPilot Layout (TL)" });

    const titleMetrics = await Promise.all(
      items.map((item) =>
        page
          .locator(`[data-test-id="kanban-card-title-${item.id}"]`)
          .evaluate((element) => {
            const styles = getComputedStyle(element);
            const rect = element.getBoundingClientRect();

            return {
              height: rect.height,
              lineHeight: Number.parseFloat(styles.lineHeight),
              overflow: styles.overflow,
            };
          }),
      ),
    );
    const cardHeights = await Promise.all(
      items.map((item) =>
        page
          .locator(`[data-test-id="kanban-card-${item.id}"]`)
          .evaluate((element) => element.getBoundingClientRect().height),
      ),
    );

    for (const metrics of titleMetrics) {
      expect(metrics.height).toBeCloseTo(metrics.lineHeight * 2, 0);
      expect(metrics.overflow).toBe("hidden");
    }

    const [firstCardHeight, ...remainingCardHeights] = cardHeights;
    for (const height of remainingCardHeights) {
      expect(height).toBeCloseTo(firstCardHeight, 0);
    }
  });
});
