import type { ItemSummary, Status } from "../types";
import { WORKFLOW_STATUSES } from "../types";
import { TYPE_ORDER } from "../types/labels";

export function resolveDropTarget(
  overId: string,
  items: ItemSummary[],
): Status | undefined {
  const direct = WORKFLOW_STATUSES.find((s) => s === overId);
  if (direct) return direct;
  const overItem = items.find((i) => i.id === overId);
  return overItem?.status;
}

export function sortItems(items: ItemSummary[]): ItemSummary[] {
  return [...items].sort((a, b) => {
    const typeCompare =
      (TYPE_ORDER[a.type] ?? 99) - (TYPE_ORDER[b.type] ?? 99);
    if (typeCompare !== 0) return typeCompare;

    const aNum = parseInt(a.id.split("-").pop() ?? "0", 10);
    const bNum = parseInt(b.id.split("-").pop() ?? "0", 10);
    return aNum - bNum;
  });
}

export function applyItemStatus(
  items: ItemSummary[],
  itemId: string,
  status: Status,
): ItemSummary[] {
  return items.map((item) =>
    item.id === itemId ? { ...item, status } : item,
  );
}

export function groupByStatus(items: ItemSummary[]): Map<Status, ItemSummary[]> {
  const groups = new Map<Status, ItemSummary[]>();
  for (const status of WORKFLOW_STATUSES) {
    groups.set(status, []);
  }
  for (const item of items) {
    if (item.status === "deleted") continue;
    const group = groups.get(item.status);
    if (group) {
      group.push(item);
    }
  }
  for (const [status, group] of groups) {
    groups.set(status, sortItems(group));
  }
  return groups;
}
