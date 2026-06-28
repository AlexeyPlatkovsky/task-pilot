import { useQuery } from "@tanstack/react-query";
import { fetchValidationReport } from "../api";
import type { ValidationFinding } from "../types";
import styles from "./ValidationPanel.module.css";

interface Props {
  projectId: string;
  onItemClick: (itemId: string) => void;
}

function FindingRow({
  finding,
  onItemClick,
}: {
  finding: ValidationFinding;
  onItemClick: (itemId: string) => void;
}) {
  return (
    <li className={styles.finding}>
      <div className={styles.findingMain}>
        <span className={styles.severity}>{finding.severity}</span>
        <span className={styles.path}>{finding.path}</span>
        <span>{finding.message}</span>
      </div>
      {finding.item_id ? (
        <button
          className={styles.openButton}
          type="button"
          onClick={() => onItemClick(finding.item_id!)}
          aria-label={`Open ${finding.item_id} validation issue`}
        >
          Open
        </button>
      ) : null}
    </li>
  );
}

export function ValidationPanel({ projectId, onItemClick }: Props) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["validation", projectId],
    queryFn: () => fetchValidationReport(projectId),
  });

  if (isLoading) {
    return <section className={styles.panel}>Checking validation...</section>;
  }

  if (error) {
    return (
      <section className={styles.panel} role="alert">
        <span>Failed to load validation results</span>
        <button type="button" onClick={() => refetch()}>
          Retry
        </button>
      </section>
    );
  }

  if (!data || data.findings.length === 0) {
    return (
      <section className={styles.panel}>
        <div className={styles.validState}>All items valid</div>
      </section>
    );
  }

  return (
    <section className={styles.panel} aria-label="Validation issues">
      <div className={styles.summary}>
        <strong>Validation issues</strong>
        <span>
          {data.summary.errors} errors, {data.summary.warnings} warnings
        </span>
      </div>
      <ul className={styles.findings}>
        {data.findings.map((finding) => (
          <FindingRow
            key={`${finding.path}:${finding.code}:${finding.field ?? ""}`}
            finding={finding}
            onItemClick={onItemClick}
          />
        ))}
      </ul>
    </section>
  );
}
