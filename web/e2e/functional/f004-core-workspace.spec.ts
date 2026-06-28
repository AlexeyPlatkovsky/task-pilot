import { expect, test, type Route } from "@playwright/test";
import {
  expectCardInColumn,
  fixtureProject,
  kanbanCard,
  kanbanColumn,
  openFixtureProject,
} from "../support/workspace";

const projectSummary = {
  id: fixtureProject.id,
  key: fixtureProject.key,
  name: fixtureProject.name,
  active: true,
};

const mockItemSummary = {
  id: "TP-9",
  title: "Delete from board",
  type: "task",
  status: "ready",
  priority: "normal",
  valid: true,
  findings: [],
};

const mockItemDetail = {
  schema_version: 1,
  id: "TP-9",
  title: "Delete from board",
  priority: "normal",
  type: "task",
  status: "ready",
  created_at: "2026-06-28T10:09:00Z",
  updated_at: "2026-06-28T10:09:00Z",
  description: "Delete scenario fixture.",
  comments: [],
  valid: true,
  findings: [],
};

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

test.describe("F004 core workspace flows", () => {
  test("shows guidance when no projects are registered", async ({ page }) => {
    await page.route("**/api/projects", (route) => fulfillJson(route, []));

    await page.goto("/");

    await expect(page.getByText("No projects registered")).toBeVisible();
    await expect(page.getByText("taskpilot init .")).toBeVisible();
  });

  test("selects a project and displays the Kanban board columns", async ({
    page,
  }) => {
    await openFixtureProject(page);

    await expect(page.getByRole("tab", { name: "Board" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await expect(
      kanbanColumn(page, "backlog").getByText("Backlog"),
    ).toBeVisible();
    await expect(kanbanColumn(page, "ready").getByText("Ready")).toBeVisible();
    await expect(
      kanbanColumn(page, "in_progress").getByText("In Progress"),
    ).toBeVisible();
    await expect(kanbanColumn(page, "done").getByText("Done")).toBeVisible();
    await expect(
      kanbanColumn(page, "cancelled").getByText("Cancelled"),
    ).toBeVisible();
  });

  test("opens an item detail modal in read mode", async ({ page }) => {
    await openFixtureProject(page);

    await kanbanCard(page, "TP-1").click();

    const dialog = page.getByRole("dialog", {
      name: "TP-1: Launch advanced workspace",
    });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText("Epic", { exact: true })).toBeVisible();
    await expect(dialog.getByText("Ready", { exact: true })).toBeVisible();
    await expect(dialog.getByText("High", { exact: true })).toBeVisible();
    await expect(dialog.getByText("Parent item for the functional e2e hierarchy."))
      .toBeVisible();
    await expect(dialog.getByRole("button", { name: "Edit" })).toBeVisible();
    await expect(dialog.getByRole("button", { name: "Delete" })).toBeVisible();
  });

  test("edits item status and moves the card to the target column", async ({
    page,
  }) => {
    await openFixtureProject(page);
    await expectCardInColumn(page, "TP-1", "ready");

    await kanbanCard(page, "TP-1").click();
    await page.getByRole("button", { name: "Edit" }).click();
    await page.getByLabel("Status").selectOption("in_progress");
    await page.getByRole("button", { name: "Save" }).click();

    await expect(
      page
        .getByRole("dialog", { name: "TP-1: Launch advanced workspace" })
        .getByText("In Progress", { exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Close" }).click();
    await expectCardInColumn(page, "TP-1", "in_progress");
    await expect(kanbanColumn(page, "ready").locator('[data-item-id="TP-1"]'))
      .toBeHidden();
  });

  test("deletes an item after confirmation and removes it from the board", async ({
    page,
  }) => {
    let items = [mockItemSummary];

    await page.route("**/api/projects", (route) =>
      fulfillJson(route, [projectSummary]),
    );
    await page.route("**/api/projects/taskpilot-e2e/validate", (route) =>
      fulfillJson(route, {
        ok: true,
        summary: { errors: 0, warnings: 0 },
        findings: [],
      }),
    );
    await page.route("**/api/projects/taskpilot-e2e/items", (route) =>
      fulfillJson(route, items),
    );
    await page.route("**/api/projects/taskpilot-e2e/items/TP-9", (route) =>
      fulfillJson(route, {
        ...mockItemDetail,
        status: items[0]?.status ?? "deleted",
      }),
    );
    await page.route(
      "**/api/projects/taskpilot-e2e/items/TP-9",
      async (route) => {
        if (route.request().method() !== "PATCH") {
          await route.fallback();
          return;
        }
        items = [];
        await fulfillJson(route, { ...mockItemDetail, status: "deleted" });
      },
    );

    await openFixtureProject(page);
    await expectCardInColumn(page, "TP-9", "ready");

    await kanbanCard(page, "TP-9").click();
    await page.getByRole("button", { name: "Delete" }).click();
    await expect(
      page.getByRole("alertdialog", { name: "Delete this item?" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Delete" }).click();

    await expect(kanbanCard(page, "TP-9")).toBeHidden();
  });

  test("shows an empty board prompt for a project with zero items", async ({
    page,
  }) => {
    await page.route("**/api/projects", (route) =>
      fulfillJson(route, [projectSummary]),
    );
    await page.route("**/api/projects/taskpilot-e2e/items", (route) =>
      fulfillJson(route, []),
    );
    await page.route("**/api/projects/taskpilot-e2e/validate", (route) =>
      fulfillJson(route, {
        ok: true,
        summary: { errors: 0, warnings: 0 },
        findings: [],
      }),
    );

    await openFixtureProject(page);

    await expect(page.getByText("No items yet.")).toBeVisible();
    await expect(page.getByText(/taskpilot item create/)).toBeVisible();
  });
});
