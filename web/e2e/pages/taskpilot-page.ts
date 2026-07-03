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

  async selectTheme(theme: "light" | "dark") {
    await this.selectDropdownOption(
      "theme-switcher",
      theme === "light" ? "Light" : "Dark",
    );
  }

  async expectTheme(theme: "light" | "dark") {
    await expect(this.page.locator("html")).toHaveAttribute(
      "data-theme",
      theme,
    );
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
  }: {
    itemId: string;
    title: string;
    type: string;
    status: string;
    priority: string;
    description: string;
  }) {
    const modal = this.itemModal(itemId);
    await expect(modal).toBeVisible();
    await expect(modal).toContainText(`${itemId}: ${title}`);
    await expect(modal).toContainText(type);
    await expect(modal).toContainText(status);
    await expect(modal).toContainText(priority);
    await expect(modal).toContainText(description);
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
    await expect(this.itemModal(itemId)).toContainText(`${itemId}: ${title}`);
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

  private kanbanCard(itemId: string): Locator {
    return this.byTestId(`kanban-card-${itemId}`);
  }

  private itemModal(itemId: string): Locator {
    return this.byTestId(`item-modal-${itemId}`);
  }
}
