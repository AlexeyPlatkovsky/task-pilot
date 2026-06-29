import { useQuery } from "@tanstack/react-query";
import { fetchValidationReport } from "../api";
import styles from "./ValidationStatus.module.css";

interface Props {
  projectId: string | null;
}

export function ValidationStatus({ projectId }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["validation", projectId],
    queryFn: () => fetchValidationReport(projectId!),
    enabled: !!projectId,
  });

  if (!projectId || isLoading || error) {
    return <div className={styles.status} />;
  }

  if (!data || data.findings.length === 0) {
    return (
      <div className={styles.status} data-test-id="validation-valid-state">
        <span className={styles.valid}>All items valid</span>
      </div>
    );
  }

  return (
    <div className={styles.status}>
      <span className={styles.issues}>
        {data.summary.errors} err{data.summary.errors !== 1 ? "s" : ""},{" "}
        {data.summary.warnings} warn{data.summary.warnings !== 1 ? "s" : ""}
      </span>
    </div>
  );
}
