import { useState, useCallback, useMemo } from "react";
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
import { DropdownSelect } from "./DropdownSelect";
import { FilterBar } from "./FilterBar";
import type { BoardFilters } from "./filters";
import {
  DEFAULT_BOARD_FILTERS,
  TYPE_FILTER_OPTIONS,
  PRIORITY_FILTER_OPTIONS,
  UPDATED_FILTER_OPTIONS,
  CREATED_FILTER_OPTIONS,
  filterReferenceTimeForItems,
  isWithinTimeRange,
} from "./filters";
import styles from "./KanbanBoard.module.css";

interface Props {
  projectId: string;
  now?: Date;
}

export function KanbanBoard({ projectId, now }: Props) {
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [activeItem, setActiveItem] = useState<ItemSummary | null>(null);
  const [droppedItemId, setDroppedItemId] = useState<string | null>(null);
  const [boardFilters, setBoardFilters] = useState<BoardFilters>(DEFAULT_BOARD_FILTERS);
  const [hiddenStatuses, setHiddenStatuses] = useState<Set<Status>>(new Set());

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
  const filterNow = useMemo(
    () => filterReferenceTimeForItems(items, now),
    [items, now],
  );

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

  const toggleCancelled = useCallback(() => {
    setHiddenStatuses((prev) => {
      const next = new Set(prev);
      if (next.has("cancelled")) {
        next.delete("cancelled");
      } else {
        next.add("cancelled");
      }
      return next;
    });
  }, []);

  const hasActiveBoardFilters =
    boardFilters.type !== DEFAULT_BOARD_FILTERS.type ||
    boardFilters.priority !== DEFAULT_BOARD_FILTERS.priority ||
    boardFilters.updatedRange !== DEFAULT_BOARD_FILTERS.updatedRange ||
    boardFilters.createdRange !== DEFAULT_BOARD_FILTERS.createdRange;

  const hasHiddenColumns = hiddenStatuses.size > 0;

  const filteredItems = useMemo(
    () =>
      (items ?? []).filter((item) => {
        if (boardFilters.type && item.type !== boardFilters.type) return false;
        if (boardFilters.priority && item.priority !== boardFilters.priority) return false;
        if (!isWithinTimeRange(item, boardFilters.updatedRange, "updated_at", filterNow)) return false;
        if (!isWithinTimeRange(item, boardFilters.createdRange, "created_at", filterNow)) return false;
        return true;
      }),
    [items, boardFilters, filterNow],
  );

  const groups = groupByStatus(filteredItems);
  const hasItems = (items?.length ?? 0) > 0;
  const allColumnsEmpty = Array.from(groups.values()).every((g) => g.length === 0);
  const isEmpty = !hasItems;
  const showEmptyPrompt = isEmpty;
  const showFilteredEmpty = hasItems && allColumnsEmpty;

  // Visible columns: exclude hidden statuses but still check them for empty prompt
  const visibleStatuses = WORKFLOW_STATUSES.filter(
    (status) => !hiddenStatuses.has(status),
  );

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
      <FilterBar
        hasActiveFilters={hasActiveBoardFilters || hasHiddenColumns}
        onClear={() => {
          setBoardFilters(DEFAULT_BOARD_FILTERS);
          setHiddenStatuses(new Set());
        }}
        ariaLabel="Board filters"
        dataTestId="kanban-board-filters"
      >
        <DropdownSelect
          id="board-filter-type"
          label="Type"
          value={boardFilters.type}
          options={TYPE_FILTER_OPTIONS}
          fieldDataTestId="board-filter-field"
          onChange={(type) => setBoardFilters((current) => ({ ...current, type }))}
        />
        <DropdownSelect
          id="board-filter-priority"
          label="Priority"
          value={boardFilters.priority}
          options={PRIORITY_FILTER_OPTIONS}
          fieldDataTestId="board-filter-field"
          onChange={(priority) => setBoardFilters((current) => ({ ...current, priority }))}
        />
        <DropdownSelect
          id="board-filter-updated"
          label="Updated"
          value={boardFilters.updatedRange}
          options={UPDATED_FILTER_OPTIONS}
          fieldDataTestId="board-filter-field"
          onChange={(updatedRange) => setBoardFilters((current) => ({ ...current, updatedRange }))}
        />
        <DropdownSelect
          id="board-filter-created"
          label="Created"
          value={boardFilters.createdRange}
          options={CREATED_FILTER_OPTIONS}
          fieldDataTestId="board-filter-field"
          onChange={(createdRange) => setBoardFilters((current) => ({ ...current, createdRange }))}
        />
      </FilterBar>

      <DndContext
        sensors={sensors}
        collisionDetection={rectIntersection}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className={styles.board} data-test-id="kanban-board">
          {visibleStatuses.map((status) => {
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
          <button
            className={styles.columnToggle}
            type="button"
            onClick={toggleCancelled}
            data-test-id="kanban-toggle-cancelled"
            title={hiddenStatuses.has("cancelled") ? "Show Cancelled column" : "Hide Cancelled column"}
          >
            {hiddenStatuses.has("cancelled") ? "+ Cancelled" : "− Cancelled"}
          </button>
          {showEmptyPrompt && (
            <div className={styles.emptyPrompt} data-test-id="kanban-empty-prompt">
              <p>No items yet.</p>
              <p>
                Create your first item with:{" "}
                <code>taskpilot item create</code>
              </p>
            </div>
          )}
          {showFilteredEmpty && (
            <div className={styles.filteredEmpty} data-test-id="kanban-filtered-empty">
              No items match the selected filters.
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
