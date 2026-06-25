import { useQuery } from "@tanstack/react-query";
import { fetchItems } from "../api";
import type { ItemSummary, Status } from "../types";
import { WORKFLOW_STATUSES } from "../types";
import { KanbanColumn } from "./KanbanColumn";
import styles from "./KanbanBoard.module.css";

interface Props {
  projectId: string;
}

const STATUS_LABELS: Record<Status, string> = {
  backlog: "Backlog",
  ready: "Ready",
  in_progress: "In Progress",
  done: "Done",
  cancelled: "Cancelled",
  deleted: "Deleted",
};

const TYPE_ORDER: Record<string, number> = {
  epic: 0,
  feature: 1,
  task: 2,
  bug: 3,
};

function sortItems(items: ItemSummary[]): ItemSummary[] {
  return [...items].sort((a, b) => {
    const typeCompare = (TYPE_ORDER[a.type] ?? 99) - (TYPE_ORDER[b.type] ?? 99);
    if (typeCompare !== 0) return typeCompare;

    const aNum = parseInt(a.id.split("-").pop() ?? "0", 10);
    const bNum = parseInt(b.id.split("-").pop() ?? "0", 10);
    return aNum - bNum;
  });
}

function groupByStatus(items: ItemSummary[]): Map<Status, ItemSummary[]> {
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

export function KanbanBoard({ projectId }: Props) {
  const {
    data: items,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["items", projectId],
    queryFn: () => fetchItems(projectId),
  });

  if (isLoading) {
    return <div className={styles.board}>Loading items...</div>;
  }

  if (error) {
    return (
      <div className={styles.board}>
        <div className={styles.error}>
          <p>Failed to load items</p>
          <button type="button" onClick={() => refetch()}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  const groups = groupByStatus(items ?? []);

  const isEmpty = Array.from(groups.values()).every((g) => g.length === 0);

  return (
    <div className={styles.board}>
      {WORKFLOW_STATUSES.map((status) => (
        <KanbanColumn
          key={status}
          status={status}
          label={STATUS_LABELS[status]}
          items={groups.get(status) ?? []}
        />
      ))}
      {isEmpty && (
        <div className={styles.emptyPrompt}>
          <p>No items yet.</p>
          <p>
            Create your first item with: <code>taskpilot item create</code>
          </p>
        </div>
      )}
    </div>
  );
}
