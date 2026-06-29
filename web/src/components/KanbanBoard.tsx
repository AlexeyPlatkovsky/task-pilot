import { useState, useCallback } from "react";
import {
  DndContext,
  DragOverlay,
  rectIntersection,
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
import { STATUS_LABELS } from "../types/labels";
import { KanbanColumn } from "./KanbanColumn";
import { KanbanCard } from "./KanbanCard";
import { ItemModal } from "./ItemModal";
import { LoadingSpinner } from "./ui/LoadingSpinner";
import {
  applyItemStatus,
  resolveDropTarget,
  groupByStatus,
} from "./kanban-utils";
import styles from "./KanbanBoard.module.css";

interface Props {
  projectId: string;
}

export function KanbanBoard({ projectId }: Props) {
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [activeItem, setActiveItem] = useState<ItemSummary | null>(null);
  const [droppedItemId, setDroppedItemId] = useState<string | null>(null);

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

  const { mutate, error: mutationError } = useMutation({
    mutationFn: ({
      itemId,
      status,
    }: {
      itemId: string;
      status: Status;
    }) => updateItem(projectId, itemId, { status }),
    onSuccess: (_updatedItem, { itemId, status }) => {
      queryClient.setQueryData<ItemSummary[]>(
        ["items", projectId],
        (current) =>
          current ? applyItemStatus(current, itemId, status) : current,
      );
      setActiveItem(null);
      setDroppedItemId(null);
      void queryClient.invalidateQueries({ queryKey: ["items", projectId] });
      if (selectedItemId) {
        void queryClient.invalidateQueries({
          queryKey: ["item", projectId, selectedItemId],
        });
      }
    },
    onError: () => {
      setActiveItem(null);
      setDroppedItemId(null);
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

      if (!over) {
        setActiveItem(null);
        return;
      }

      const activeId = active.id as string;
      const overId = over.id as string;

      const activeItem = items?.find((i) => i.id === activeId);
      if (!activeItem || !activeItem.valid) {
        setActiveItem(null);
        return;
      }

      const targetStatus = items
        ? resolveDropTarget(overId, items)
        : undefined;
      if (targetStatus && activeItem.status !== targetStatus) {
        setDroppedItemId(activeId);
        setActiveItem(null);
        mutate({ itemId: activeId, status: targetStatus });
      } else {
        setActiveItem(null);
      }
    },
    [items, mutate],
  );

  const groups = groupByStatus(items ?? []);
  const isEmpty = Array.from(groups.values()).every((g) => g.length === 0);

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <LoadingSpinner label="Loading items..." />
      </div>
    );
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
        collisionDetection={rectIntersection}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className={styles.board} data-test-id="kanban-board">
          {WORKFLOW_STATUSES.map((status) => {
            const columnItems = groups.get(status) ?? [];
            return (
              <KanbanColumn
                key={status}
                status={status}
                label={STATUS_LABELS[status]}
                items={columnItems}
                onItemClick={setSelectedItemId}
                droppedItemId={droppedItemId}
                activeDraggedItemId={activeItem?.id ?? null}
              />
            );
          })}
          {isEmpty && (
            <div className={styles.emptyPrompt} data-test-id="kanban-empty-prompt">
              <p>No items yet.</p>
              <p>
                Create your first item with:{" "}
                <code>taskpilot item create</code>
              </p>
            </div>
          )}
        </div>

        <DragOverlay dropAnimation={null}>
          {activeItem ? <KanbanCard item={activeItem} /> : null}
        </DragOverlay>
      </DndContext>

      {mutationError && (
        <div className={styles.mutationError} role="alert">
          Failed to update item status. Please try again.
        </div>
      )}

      <ItemModal
        projectId={projectId}
        itemId={selectedItemId}
        onClose={() => setSelectedItemId(null)}
      />
    </>
  );
}
