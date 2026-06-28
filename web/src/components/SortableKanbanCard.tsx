import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { ItemSummary } from "../types";
import { KanbanCard } from "./KanbanCard";
import styles from "./SortableKanbanCard.module.css";

interface Props {
  item: ItemSummary;
  onClick?: (itemId: string) => void;
}

export function SortableKanbanCard({ item, onClick }: Props) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: item.id,
    disabled: !item.valid,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`${styles.wrapper} ${isDragging ? styles.dragging : ""}`}
      {...attributes}
      {...listeners}
    >
      <KanbanCard item={item} onClick={onClick} />
    </div>
  );
}
