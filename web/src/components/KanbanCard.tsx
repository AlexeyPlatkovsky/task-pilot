import { Layers, Zap, CheckSquare, Bug, type LucideIcon } from "lucide-react";
import type { ItemSummary, ItemType } from "../types";
import { Icon } from "./ui/Icon";
import styles from "./KanbanCard.module.css";

interface Props {
  item: ItemSummary;
  onClick?: (itemId: string) => void;
}

const TYPE_ICON_COMPONENTS: Record<ItemType, LucideIcon> = {
  epic: Layers,
  feature: Zap,
  task: CheckSquare,
  bug: Bug,
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
      data-test-id={`kanban-card-${item.id}`}
      onClick={handleClick}
      onKeyDown={item.valid && onClick ? handleKeyDown : undefined}
      aria-label={`${item.id}: ${item.title}`}
    >
      <div className={styles.header}>
        <span className={styles.id}>{item.id}</span>
        <span className={styles.type} title={item.type}>
          <Icon icon={TYPE_ICON_COMPONENTS[item.type]} label={item.type} />
          {item.type}
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
