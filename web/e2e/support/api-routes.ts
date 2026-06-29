import type { Page, Route } from "@playwright/test";
import { fixtureProject } from "../pages/taskpilot-page";

export const projectSummary = {
  id: fixtureProject.id,
  key: fixtureProject.key,
  name: fixtureProject.name,
  active: true,
};

export async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

export async function mockNoProjects(page: Page) {
  await page.route("**/api/projects", (route) => fulfillJson(route, []));
}

export async function mockValidationOk(page: Page) {
  await page.route("**/api/projects/taskpilot-e2e/validate", (route) =>
    fulfillJson(route, {
      ok: true,
      summary: { errors: 0, warnings: 0 },
      findings: [],
    }),
  );
}

export async function mockProjectList(page: Page) {
  await page.route("**/api/projects", (route) =>
    fulfillJson(route, [projectSummary]),
  );
}

export async function mockEmptyProject(page: Page) {
  await mockProjectList(page);
  await mockValidationOk(page);
  await page.route("**/api/projects/taskpilot-e2e/items", (route) =>
    fulfillJson(route, []),
  );
}
