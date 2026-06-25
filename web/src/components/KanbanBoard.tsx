import { useState, useCallback } from "react";
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchItems, updateItem } from "../api";
import type { ItemSummary, Status } from "../types";
import { WORKFLOW_STATUSES } from "../types";
import { STATUS_LABELS, TYPE_ORDER } from "../types/labels";
import { KanbanColumn } from "./KanbanColumn";
import { KanbanCard } from "./KanbanCard";
import { ItemModal } from "./ItemModal";
import styles from "./KanbanBoard.module.css";

interface Props {
  projectId: string;
}

function sortItems(items: ItemSummary[]): ItemSummary[] {
  return [...items].sort((a, b) => {
    const typeCompare =
      (TYPE_ORDER[a.type] ?? 99) - (TYPE_ORDER[b.type] ?? 99);
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
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [activeItem, setActiveItem] = useState<ItemSummary | null>(null);

  const queryClient = useQueryClient();

  const {
    data: items,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["items", projectId],
    queryFn: () => fetchItems(projectId),
  });

  const mutation = useMutation({
    mutationFn: ({
      itemId,
      status,
    }: {
      itemId: string;
      status: Status;
    }) => updateItem(projectId, itemId, { status }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["items", projectId] });
      if (selectedItemId) {
        void queryClient.invalidateQueries({
          queryKey: ["item", projectId, selectedItemId],
        });
      }
    },
  });

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor),
  );

  const handleDragStart = useCallback(
    (event: DragStartEvent) => {
      const item = items?.find((i) => i.id === event.active.id);
      if (item && item.valid) {
        setActiveItem(item);
      }
    },
    [items],
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      setActiveItem(null);

      if (!over) return;

      const activeId = active.id as string;
      const overId = over.id as string;

      const activeItem = items?.find((i) => i.id === activeId);
      if (!activeItem || !activeItem.valid) return;

      const overStatus = WORKFLOW_STATUSES.find((s) => s === overId);
      if (overStatus && activeItem.status !== overStatus) {
        mutation.mutate({ itemId: activeId, status: overStatus });
      }
    },
    [items, mutation],
  );

  const groups = groupByStatus(items ?? []);
  const isEmpty = Array.from(groups.values()).every((g) => g.length === 0);

  if (isLoading) {
    return <div className={styles.loading}>Loading items...</div>;
  }

  if (error) {
    return (
      <div className={styles.error}>
        <p>Failed to load items</p>
        <button type="button" onClick={() => refetch()}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className={styles.board}>
          {WORKFLOW_STATUSES.map((status) => {
            const columnItems = groups.get(status) ?? [];
            return (
              <KanbanColumn
                key={status}
                status={status}
                label={STATUS_LABELS[status]}
                items={columnItems}
                onItemClick={setSelectedItemId}
              />
            );
          })}
          {isEmpty && (
            <div className={styles.emptyPrompt}>
              <p>No items yet.</p>
              <p>
                Create your first item with:{" "}
                <code>taskpilot item create</code>
              </p>
            </div>
          )}
        </div>

        <DragOverlay>
          {activeItem ? <KanbanCard item={activeItem} /> : null}
        </DragOverlay>
      </DndContext>

      <ItemModal
        projectId={projectId}
        itemId={selectedItemId}
        onClose={() => setSelectedItemId(null)}
      />
    </>
  );
}
