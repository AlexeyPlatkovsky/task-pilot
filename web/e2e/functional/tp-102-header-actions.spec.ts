import { test } from "@playwright/test";
import { fixtureProject, TaskPilotPage } from "../pages/taskpilot-page";

// Spec 0010: header theme toggle persistence (TP-102), Doctor (TP-139), and
// project unregister (TP-138) against the real REST API.

const scratch = { name: "Scratch E2E", key: "SC" } as const;

test.describe("header project actions", () => {
  test("theme choice persists across reload and auto restores OS mode", async ({
    page,
  }) => {
    const app = new TaskPilotPage(page);
    await app.open();
    await app.expectTheme("auto", { firstVisit: true });

    await app.selectTheme("dark");
    await app.expectTheme("dark");
    await app.reload();
    await app.expectTheme("dark");

    await app.selectTheme("light");
    await app.reload();
    await app.expectTheme("light");

    await app.selectTheme("auto");
    await app.reload();
    await app.expectTheme("auto");
  });

  test("doctor repairs a dangling link, then the project is unregistered", async ({
    page,
  }) => {
    const app = new TaskPilotPage(page);
    await app.openProject(scratch.name, scratch.key);
    await app.expectValidationIssues();

    await app.openDoctor();
    await app.expectDoctorSafeFix("Remove links.blocks -> SC-99 from SC-1");
    await app.applyDoctorFixes(1);
    await app.closeDoctor();
    await app.expectValidationClean();

    await app.unregisterSelectedProject(scratch.name, { confirm: false });
    await app.expectSelectedProject(scratch.name, scratch.key);

    await app.unregisterSelectedProject(scratch.name, { confirm: true });
    await app.expectSelectedProject(fixtureProject.name, fixtureProject.key);
    await app.expectProjectOptions(
      [`${fixtureProject.name} (${fixtureProject.key})`],
      [`${scratch.name} (${scratch.key})`],
    );
  });
});
