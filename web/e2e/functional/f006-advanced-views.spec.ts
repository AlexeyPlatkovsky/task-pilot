import { test } from "@playwright/test";
import { TaskPilotPage } from "../pages/taskpilot-page";

test.describe("F006 advanced workspace views", () => {
  test("switches views, filters and sorts the list, and opens a tree item", async ({
    page,
  }) => {
    const app = new TaskPilotPage(page);
    await app.openFixtureProject();
    await app.expectBoardTabSelected();
    await app.expectCardVisible("TP-1", "Launch advanced workspace");

    await app.switchToListView();
    await app.expectListReady();
    await app.filterListByType("bug");
    await app.expectListItemVisible("TP-3");
    await app.expectListItemHidden("TP-2");

    await app.clearListTypeFilter();
    await app.sortListById();
    await app.expectFirstListRow("TP-1");
    await app.sortListById();
    await app.expectFirstListRow("TP-3");

    await app.switchToTreeView();
    await app.expandTreeItem("TP-1");
    await app.expandTreeItem("TP-2");
    await app.openTreeItem("TP-3");

    await app.expectModalVisible("TP-3", "Fix tree regression");
    await app.expectModalText("TP-3", "Leaf item opened from the tree view.");
  });
});
