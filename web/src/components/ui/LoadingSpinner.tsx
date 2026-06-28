import styles from "./LoadingSpinner.module.css";

interface Props {
  label?: string;
}

export function LoadingSpinner({ label = "Loading..." }: Props) {
  return (
    <div className={styles.wrapper} role="status" aria-label={label}>
      <div className={styles.spinner} />
      <span className={styles.label}>{label}</span>
    </div>
  );
}
