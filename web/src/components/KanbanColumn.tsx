import type { ItemSummary, Status } from "../types";
import { KanbanCard } from "./KanbanCard";
import styles from "./KanbanColumn.module.css";

interface Props {
  status: Status;
  label: string;
  items: ItemSummary[];
  onItemClick?: (itemId: string) => void;
}

export function KanbanColumn({ status, label, items, onItemClick }: Props) {
  return (
    <div className={styles.column} data-status={status}>
      <div className={styles.header}>
        <h3 className={styles.title}>{label}</h3>
        <span className={styles.count}>{items.length}</span>
      </div>
      <div className={styles.list} role="list">
        {items.length === 0 ? (
          <div className={styles.empty}>No items</div>
        ) : (
          items.map((item) => (
            <KanbanCard key={item.id} item={item} onClick={onItemClick} />
          ))
        )}
      </div>
    </div>
  );
}
