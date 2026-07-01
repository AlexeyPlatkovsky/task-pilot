import type { ReactNode } from "react";
import styles from "./FilterBar.module.css";

interface Props {
  children: ReactNode;
  hasActiveFilters: boolean;
  onClear: () => void;
  ariaLabel?: string;
  dataTestId?: string;
}

export function FilterBar({
  children,
  hasActiveFilters,
  onClear,
  ariaLabel = "Filters",
  dataTestId,
}: Props) {
  return (
    <div
      className={styles.filterBar}
      aria-label={ariaLabel}
      data-test-id={dataTestId}
    >
      {children}
      <div className={styles.filterActions} data-position="trailing">
        <button
          className={styles.clearButton}
          type="button"
          disabled={!hasActiveFilters}
          onClick={onClear}
          aria-label="Clear filters"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
