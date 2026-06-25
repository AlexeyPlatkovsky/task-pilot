import type { ItemSummary, ItemType } from "../types";
import styles from "./KanbanCard.module.css";

interface Props {
  item: ItemSummary;
  onClick?: (itemId: string) => void;
}

const TYPE_ICONS: Record<ItemType, string> = {
  epic: "\u2B1B",
  feature: "\u25B6",
  task: "\u25A1",
  bug: "\u26A0",
};

export function KanbanCard({ item, onClick }: Props) {
  const handleClick = () => {
    if (item.valid && onClick) {
      onClick(item.id);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <div
      className={`${styles.card} ${!item.valid ? styles.invalid : ""}`}
      data-item-id={item.id}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role={item.valid ? "button" : undefined}
      tabIndex={item.valid ? 0 : undefined}
      aria-label={`${item.id}: ${item.title}`}
    >
      <div className={styles.header}>
        <span className={styles.id}>{item.id}</span>
        <span className={styles.type} title={item.type}>
          {TYPE_ICONS[item.type]} {item.type}
        </span>
      </div>
      <div className={styles.title}>{item.title}</div>
      <div className={styles.footer}>
        <span className={`${styles.priority} ${styles[item.priority]}`}>
          {item.priority}
        </span>
        {!item.valid && (
          <span className={styles.invalidBadge} title="Invalid item">
            !
          </span>
        )}
      </div>
    </div>
  );
}
