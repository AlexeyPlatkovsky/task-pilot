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
}

export function KanbanColumn({ status, label, items, onItemClick }: Props) {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
  });

  const itemIds = items.map((item) => item.id);

  return (
    <div
      className={`${styles.column} ${isOver ? styles.dropTarget : ""}`}
      data-status={status}
    >
      <div className={styles.header}>
        <h3 className={styles.title}>{label}</h3>
        <span className={styles.count}>{items.length}</span>
      </div>
      <div ref={setNodeRef} className={styles.list} role="list">
        <SortableContext items={itemIds} strategy={verticalListSortingStrategy}>
          {items.length === 0 ? (
            <div className={styles.empty}>No items</div>
          ) : (
            items.map((item) => (
              <SortableKanbanCard
                key={item.id}
                item={item}
                onClick={onItemClick}
              />
            ))
          )}
        </SortableContext>
      </div>
    </div>
  );
}
