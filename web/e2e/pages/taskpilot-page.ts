import { expect, type Locator, type Page } from "@playwright/test";

export const fixtureProject = {
  id: "taskpilot-e2e",
  key: "TP",
  name: "TaskPilot E2E",
} as const;

export class TaskPilotPage {
  constructor(private readonly page: Page) {}

  async open() {
    await this.page.goto("/");
    await expect(this.byTestId("app-title")).toBeVisible();
  }

  async openWithNoProjects() {
    await this.open();
    await expect(this.byTestId("project-selector-empty")).toContainText(
      "No projects registered",
    );
    await expect(this.byTestId("project-selector-empty")).toContainText(
      "taskpilot init .",
    );
  }

  async openFixtureProject() {
    await this.open();
    await this.selectDropdownOption(
      "project-selector",
      `${fixtureProject.name} (${fixtureProject.key})`,
    );
    await expect(this.byTestId("validation-valid-state")).toContainText(
      "All items valid",
    );
  }

  async selectTheme(theme: "auto" | "light" | "dark") {
    const option = this.byTestId(`theme-option-${theme}`);
    await expect(option).toHaveAccessibleName(`${capitalize(theme)} theme`);
    await option.click();
  }

  async expectTheme(
    theme: "auto" | "light" | "dark",
    { firstVisit = false }: { firstVisit?: boolean } = {},
  ) {
    await expect(this.byTestId(`theme-option-${theme}`)).toHaveAttribute(
      "aria-checked",
      "true",
    );
    const stored = await this.page.evaluate(() =>
      window.localStorage.getItem("taskpilot.theme"),
    );
    // A first visit stores nothing; "auto" is the documented fallback.
    expect(stored).toBe(firstVisit ? null : theme);
    if (theme === "auto") {
      await expect(this.page.locator("html")).not.toHaveAttribute("data-theme", /.*/);
    } else {
      await expect(this.page.locator("html")).toHaveAttribute("data-theme", theme);
    }
  }

  async reload() {
    await this.page.reload();
    await expect(this.byTestId("app-title")).toBeVisible();
  }

  async openProject(name: string, key: string) {
    await this.open();
    await this.selectDropdownOption("project-selector", `${name} (${key})`);
  }

  async expectValidationIssues() {
    await expect(this.byTestId("validation-issues-state")).toBeVisible();
  }

  async expectValidationClean() {
    await expect(this.byTestId("validation-valid-state")).toContainText(
      "All items valid",
    );
  }

  async openDoctor() {
    const button = this.byTestId("header-doctor-button");
    await expect(button).toHaveAccessibleName("Doctor");
    await button.click();
    await expect(this.doctorDialog()).toBeVisible();
  }

  async expectDoctorSafeFix(description: string) {
    await expect(this.byTestId("doctor-safe-fixes")).toContainText(description);
  }

  async applyDoctorFixes(count: number) {
    const label = `Apply ${count} ${count === 1 ? "fix" : "fixes"}`;
    const apply = this.byTestId("doctor-apply");
    await expect(apply).toHaveText(label);
    await apply.click();
    await expect(this.byTestId("doctor-apply-result")).toContainText(
      `Applied ${count} ${count === 1 ? "fix" : "fixes"}.`,
    );
    await expect(this.doctorDialog()).toContainText("No automatic fixes available.");
  }

  async closeDoctor() {
    await this.byTestId("doctor-close").click();
    await expect(this.doctorDialog()).toBeHidden();
  }

  async unregisterSelectedProject(name: string, { confirm }: { confirm: boolean }) {
    const button = this.byTestId("header-unregister-button");
    await expect(button).toHaveAccessibleName("Unregister project");
    await button.click();
    const dialog = this.byTestId("unregister-project-dialog");
    await expect(dialog).toHaveAccessibleName(`Unregister ${name}?`);
    await expect(dialog).toContainText(".taskpilot/");
    await this.byTestId(
      confirm ? "unregister-project-submit" : "unregister-project-cancel",
    ).click();
    await expect(dialog).toBeHidden();
  }

  async expectSelectedProject(name: string, key: string) {
    await expect(this.byTestId("project-selector")).toHaveAccessibleName(
      `Project: ${name} (${key})`,
    );
  }

  async expectProjectOptions(present: string[], absent: string[]) {
    await this.byTestId("project-selector").click();
    const listbox = this.page.getByRole("listbox");
    for (const option of present) {
      await expect(listbox.getByRole("option", { name: option })).toBeVisible();
    }
    for (const option of absent) {
      await expect(listbox.getByRole("option", { name: option })).toHaveCount(0);
    }
    await this.page.keyboard.press("Escape");
  }

  async expectBoardTabSelected() {
    await expect(this.byTestId("workspace-tab-board")).toHaveAttribute(
      "aria-selected",
      "true",
    );
  }

  async expectKanbanColumnsVisible() {
    for (const [status, label] of [
      ["backlog", "Backlog"],
      ["ready", "Ready"],
      ["in_progress", "In Progress"],
      ["done", "Done"],
      ["cancelled", "Cancelled"],
    ] as const) {
      await expect(this.kanbanColumn(status)).toContainText(label);
    }
  }

  async expectCardVisible(itemId: string, title?: string) {
    const card = this.kanbanCard(itemId);
    await expect(card).toBeVisible();
    if (title) {
      await expect(card).toContainText(title);
    }
  }

  async expectCardInColumn(itemId: string, status: string) {
    await expect(
      this.kanbanColumn(status).locator(`[data-test-id="kanban-card-${itemId}"]`),
    ).toBeVisible();
  }

  async expectCardNotInColumn(itemId: string, status: string) {
    await expect(
      this.kanbanColumn(status).locator(`[data-test-id="kanban-card-${itemId}"]`),
    ).toBeHidden();
  }

  async openCard(itemId: string) {
    await this.kanbanCard(itemId).click();
  }

  async expectItemModalReadMode({
    itemId,
    title,
    type,
    status,
    priority,
    description,
    linkedTo,
  }: {
    itemId: string;
    title: string;
    type: string;
    status: string;
    priority: string;
    description: string;
    linkedTo?: string[];
  }) {
    const modal = this.itemModal(itemId);
    await expect(modal).toBeVisible();
    await expect(modal).toContainText(itemId);
    await expect(modal).toContainText(title);
    await expect(modal).toContainText(compactTypeLabel(type));
    await expect(modal).toContainText(status);
    await expect(modal).toContainText(priority);
    await expect(modal).toContainText(description);
    for (const linkedText of linkedTo ?? []) {
      await expect(modal).toContainText(linkedText);
    }
    await expect(this.byTestId("item-modal-edit")).toBeVisible();
    await expect(this.byTestId("item-modal-delete")).toBeVisible();
  }

  async editOpenItemStatus(status: string) {
    await this.byTestId("item-modal-edit").click();
    await this.byTestId("item-edit-status").selectOption(status);
    await this.byTestId("item-edit-save").click();
  }

  async expectOpenItemStatus(itemId: string, status: string) {
    await expect(this.itemModal(itemId)).toContainText(status);
  }

  async closeModal() {
    await this.byTestId("item-modal-close").click();
  }

  async deleteOpenItem() {
    await this.byTestId("item-modal-delete").click();
    await expect(this.byTestId("delete-confirm-dialog")).toBeVisible();
    await this.byTestId("delete-confirm-submit").click();
  }

  async expectCardHidden(itemId: string) {
    await expect(this.kanbanCard(itemId)).toBeHidden();
  }

  async expectEmptyBoardPrompt() {
    await expect(this.byTestId("kanban-empty-prompt")).toContainText(
      "No items yet",
    );
    await expect(this.byTestId("kanban-empty-prompt")).toContainText(
      "taskpilot item create",
    );
  }

  async switchToListView() {
    await this.byTestId("workspace-tab-list").click();
    await expect(this.byTestId("workspace-tab-list")).toHaveAttribute(
      "aria-selected",
      "true",
    );
  }

  async expectArchivedTabVisible() {
    await expect(this.byTestId("workspace-tab-archived")).toBeVisible();
  }

  async openArchivedView() {
    await this.byTestId("workspace-tab-archived").click();
  }

  async expectArchivedListVisible() {
    await expect(this.byTestId("archived-list")).toBeVisible();
  }

  async openArchivedItem(itemId: string) {
    await this.byTestId(`archived-list-open-${itemId}`).click();
  }

  async expectArchivedItemDetail(itemId: string, title: string) {
    await this.expectModalVisible(itemId, title);
    await expect(this.byTestId("item-modal-edit")).toBeHidden();
    await expect(this.byTestId("item-modal-delete")).toBeHidden();
  }

  async switchToBoard() {
    await this.byTestId("workspace-tab-board").click();
    await this.expectBoardTabSelected();
  }

  async unarchiveArchivedItem(itemId: string) {
    await this.byTestId(`unarchive-button-${itemId}`).click();
    await expect(this.byTestId("unarchive-confirm-dialog")).toBeVisible();
    await this.byTestId("unarchive-confirm-submit").click();
  }

  async expectListReady() {
    await expect(this.byTestId("item-list-table")).toBeVisible();
    await expect(this.byTestId("item-list-open-TP-2")).toBeVisible();
  }

  async filterListByType(type: string) {
    const typeLabels: Record<string, string> = {
      epic: "Epic",
      feature: "Feature",
      task: "Task",
      bug: "Bug",
    };
    await this.selectListFilterOption("type", typeLabels[type] ?? type);
  }

  async clearListTypeFilter() {
    await this.selectListFilterOption("type", "All types");
  }

  async expectListItemVisible(itemId: string) {
    await expect(this.byTestId(`item-list-open-${itemId}`)).toBeVisible();
  }

  async expectListItemHidden(itemId: string) {
    await expect(this.byTestId(`item-list-open-${itemId}`)).toBeHidden();
  }

  async sortListById() {
    await this.byTestId("item-list-sort-id").evaluate((button) =>
      (button as HTMLButtonElement).click(),
    );
  }

  async expectFirstListRow(itemId: string) {
    await expect(this.byTestId("item-list-row").first()).toHaveAttribute(
      "data-item-id",
      itemId,
    );
  }

  async openTreeItem(itemId: string) {
    await this.byTestId(`item-tree-open-${itemId}`).click();
  }

  async expectModalVisible(itemId: string, title: string) {
    await expect(this.itemModal(itemId)).toContainText(itemId);
    await expect(this.itemModal(itemId)).toContainText(title);
  }

  async expectModalText(itemId: string, text: string) {
    await expect(this.itemModal(itemId)).toContainText(text);
  }

  private byTestId(id: string): Locator {
    return this.page.locator(`[data-test-id="${id}"]`);
  }

  private async selectListFilterOption(filterId: string, option: string) {
    await this.selectDropdownOption(`item-list-filter-${filterId}`, option);
  }

  private async selectDropdownOption(testId: string, option: string) {
    await this.byTestId(testId).click();
    await this.page
      .getByRole("listbox")
      .getByRole("option", { name: option })
      .click();
  }

  private kanbanColumn(status: string): Locator {
    return this.byTestId(`kanban-column-${status}`);
  }

  private doctorDialog(): Locator {
    return this.byTestId("doctor-dialog");
  }

  private kanbanCard(itemId: string): Locator {
    return this.byTestId(`kanban-card-${itemId}`);
  }

  private itemModal(itemId: string): Locator {
    return this.byTestId(`item-modal-${itemId}`);
  }
}

function compactTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    Epic: "EPIC",
    Feature: "FEAT",
    Task: "TASK",
    Bug: "BUG",
  };
  return labels[type] ?? type;
}

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
