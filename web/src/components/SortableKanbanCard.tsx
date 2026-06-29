import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { ItemSummary } from "../types";
import { KanbanCard } from "./KanbanCard";
import styles from "./SortableKanbanCard.module.css";

interface Props {
  item: ItemSummary;
  onClick?: (itemId: string) => void;
  droppedItemId?: string | null;
  activeDraggedItemId?: string | null;
}

export function SortableKanbanCard({
  item,
  onClick,
  droppedItemId,
  activeDraggedItemId,
}: Props) {
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

  const isHidden =
    isDragging || item.id === droppedItemId || item.id === activeDraggedItemId;

  const style = {
    transform: CSS.Transform.toString(transform),
    transition: isHidden ? undefined : transition,
    opacity: isHidden ? 0 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`${styles.wrapper} ${isDragging ? styles.dragging : ""}`}
      data-test-id={`kanban-sortable-${item.id}`}
      {...attributes}
      {...listeners}
    >
      <KanbanCard item={item} onClick={onClick} />
    </div>
  );
}
