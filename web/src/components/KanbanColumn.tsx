import { useDroppable } from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import type { ItemSummary, Status } from "../types";
import { SortableKanbanCard } from "./SortableKanbanCard";
import styles from "./KanbanColumn.module.css";

interface Props {
  status: Status;
  label: string;
  items: ItemSummary[];
  onItemClick?: (itemId: string) => void;
  droppedItemId?: string | null;
  activeDraggedItemId?: string | null;
}

export function KanbanColumn({
  status,
  label,
  items,
  onItemClick,
  droppedItemId,
  activeDraggedItemId,
}: Props) {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
  });

  const itemIds = items.map((item) => item.id);

  return (
    <div
      ref={setNodeRef}
      className={`${styles.column} ${isOver ? styles.dropTarget : ""}`}
      data-status={status}
      data-test-id={`kanban-column-${status}`}
    >
      <div className={styles.header}>
        <h3 className={styles.title}>{label}</h3>
        <span className={styles.count}>{items.length}</span>
      </div>
      <div className={styles.list} role="list">
        <SortableContext items={itemIds} strategy={verticalListSortingStrategy}>
          {items.length === 0 ? (
            <div className={styles.empty}>No items</div>
          ) : (
            items.map((item) => (
              <SortableKanbanCard
                key={item.id}
                item={item}
                onClick={onItemClick}
                droppedItemId={droppedItemId}
                activeDraggedItemId={activeDraggedItemId}
              />
            ))
          )}
        </SortableContext>
      </div>
    </div>
  );
}
