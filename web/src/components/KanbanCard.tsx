import type { ItemSummary } from "../types";
import styles from "./KanbanCard.module.css";

interface Props {
  item: ItemSummary;
}

export function KanbanCard({ item }: Props) {
  return (
    <div
      className={`${styles.card} ${!item.valid ? styles.invalid : ""}`}
      data-item-id={item.id}
    >
      <div className={styles.header}>
        <span className={styles.id}>{item.id}</span>
        <span className={styles.type}>{item.type}</span>
      </div>
      <div className={styles.title}>{item.title}</div>
      <div className={styles.footer}>
        <span className={`${styles.priority} ${styles[item.priority]}`}>
          {item.priority}
        </span>
        {!item.valid && <span className={styles.invalidBadge}>!</span>}
      </div>
    </div>
  );
}
