import { test } from "@playwright/test";
import { TaskPilotPage } from "../pages/taskpilot-page";
import {
  fulfillJson,
  mockEmptyProject,
  mockNoProjects,
  mockProjectList,
  mockValidationOk,
} from "../support/api-routes";

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

test.describe("F004 core workspace flows", () => {
  test("shows guidance when no projects are registered", async ({ page }) => {
    await mockNoProjects(page);

    await new TaskPilotPage(page).openWithNoProjects();
  });

  test("selects a project and displays the Kanban board columns", async ({
    page,
  }) => {
    const app = new TaskPilotPage(page);
    await app.openFixtureProject();
    await app.expectBoardTabSelected();
    await app.expectKanbanColumnsVisible();
  });

  test("opens an item detail modal in read mode", async ({ page }) => {
    const app = new TaskPilotPage(page);
    await app.openFixtureProject();
    await app.openCard("TP-1");

    await app.expectItemModalReadMode({
      itemId: "TP-1",
      title: "Launch advanced workspace",
      type: "Epic",
      status: "Ready",
      priority: "High",
      description: "Parent item for the functional e2e hierarchy.",
      linkedTo: [
        "Linked to",
        "Child: TP-2 Build list filtering",
        "Blocks: TP-3 Fix tree regression",
        "Blocked by: TP-5 Test feature label color",
        "Related to: TP-4 Test epic label color",
      ],
    });
  });

  test("edits item status and moves the card to the target column", async ({
    page,
  }) => {
    const app = new TaskPilotPage(page);
    await app.openFixtureProject();
    await app.expectCardInColumn("TP-1", "ready");

    await app.openCard("TP-1");
    await app.editOpenItemStatus("in_progress");

    await app.expectOpenItemStatus("TP-1", "In Progress");
    await app.closeModal();
    await app.expectCardInColumn("TP-1", "in_progress");
    await app.expectCardNotInColumn("TP-1", "ready");
  });

  test("deletes an item after confirmation and removes it from the board", async ({
    page,
  }) => {
    let items = [mockItemSummary];

    await mockProjectList(page);
    await mockValidationOk(page);
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

    const app = new TaskPilotPage(page);
    await app.openFixtureProject();
    await app.expectCardInColumn("TP-9", "ready");

    await app.openCard("TP-9");
    await app.deleteOpenItem();

    await app.expectCardHidden("TP-9");
  });

  test("shows an empty board prompt for a project with zero items", async ({
    page,
  }) => {
    await mockEmptyProject(page);

    const app = new TaskPilotPage(page);
    await app.openFixtureProject();

    await app.expectEmptyBoardPrompt();
  });
});
