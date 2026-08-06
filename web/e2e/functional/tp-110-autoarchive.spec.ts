import { test } from "@playwright/test";
import { TaskPilotPage } from "../pages/taskpilot-page";

test.describe("TP-110 archived workspace", () => {
  test("always exposes Archived and opens its plain list", async ({ page }) => {
    const app = new TaskPilotPage(page);
    await app.openFixtureProject();
    await app.expectArchivedTabVisible();
    await app.openArchivedView();
    await app.expectArchivedListVisible();
  });

  test("opens archived item detail without a 404 and keeps it read-only", async ({ page }) => {
    const app = new TaskPilotPage(page);
    await app.openFixtureProject();
    await app.openArchivedView();
    await app.openArchivedItem("TP-110");
    await app.expectArchivedItemDetail("TP-110", "Archived E2E item");
  });

  test("restores an archived item to the active board after confirmation", async ({ page }) => {
    const app = new TaskPilotPage(page);
    await app.openFixtureProject();
    await app.openArchivedView();
    await app.expectArchivedListVisible();
    await app.unarchiveArchivedItem("TP-110");
    await app.expectCardHidden("TP-110");
    await app.switchToBoard();
    await app.expectCardInColumn("TP-110", "done");
  });
});
