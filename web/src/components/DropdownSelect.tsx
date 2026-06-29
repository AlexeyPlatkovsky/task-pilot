import { useState, type FocusEvent, type KeyboardEvent } from "react";
import styles from "./DropdownSelect.module.css";

export interface DropdownOption<T extends string = string> {
  value: T;
  label: string;
}

type DropdownSize = "filter" | "project" | "theme";

function selectedOptionLabel<T extends string>(
  options: readonly DropdownOption<T>[],
  value: T,
): string {
  return options.find((option) => option.value === value)?.label ?? value;
}

export function DropdownSelect<T extends string>({
  id,
  label,
  value,
  options,
  onChange,
  size = "filter",
  dataTestId,
  fieldDataTestId,
}: {
  id: string;
  label: string;
  value: T;
  options: readonly DropdownOption<T>[];
  onChange: (value: T) => void;
  size?: DropdownSize;
  dataTestId?: string;
  fieldDataTestId?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const selectedLabel = selectedOptionLabel(options, value);
  const menuId = `${id}-menu`;

  const closeOnExternalBlur = (event: FocusEvent<HTMLDivElement>) => {
    const nextTarget = event.relatedTarget;
    if (!(nextTarget instanceof Node) || !event.currentTarget.contains(nextTarget)) {
      setIsOpen(false);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      setIsOpen(false);
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setIsOpen(true);
    }
  };

  return (
    <div
      className={styles.field}
      data-test-id={fieldDataTestId ?? `${id}-field`}
      data-layout="inline"
      onBlur={closeOnExternalBlur}
      onKeyDown={handleKeyDown}
    >
      <span id={`${id}-label`} className={styles.label}>
        {label}
      </span>
      <div className={styles.anchor}>
        <button
          id={id}
          className={`${styles.button} ${styles[size]}`}
          type="button"
          data-test-id={dataTestId ?? id}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          aria-controls={isOpen ? menuId : undefined}
          aria-label={`${label}: ${selectedLabel}`}
          onClick={() => setIsOpen((current) => !current)}
        >
          <span>{selectedLabel}</span>
          <span aria-hidden="true" className={styles.chevron}>
            ▾
          </span>
        </button>
        {isOpen ? (
          <div
            id={menuId}
            className={styles.menu}
            role="listbox"
            aria-label={`${label} options`}
            data-placement="below"
            data-test-id={`${id}-menu`}
          >
            {options.map((option) => (
              <button
                key={option.value || "all"}
                className={styles.option}
                type="button"
                role="option"
                aria-selected={option.value === value}
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
              >
                {option.label}
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
