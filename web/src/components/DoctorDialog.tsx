import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { applyDoctorFixes, fetchDoctorPlan } from "../api";
import { LoadingSpinner } from "./ui/LoadingSpinner";
import dialogStyles from "./DeleteConfirmDialog.module.css";
import styles from "./DoctorDialog.module.css";

interface Props {
  projectId: string;
  onClose: () => void;
}

function fixCount(count: number): string {
  return `${count} ${count === 1 ? "fix" : "fixes"}`;
}

export function DoctorDialog({ projectId, onClose }: Props) {
  const queryClient = useQueryClient();
  const plan = useQuery({
    queryKey: ["doctor", projectId],
    queryFn: () => fetchDoctorPlan(projectId),
  });

  const apply = useMutation({
    mutationFn: () => applyDoctorFixes(projectId),
    onSuccess: () => {
      for (const queryKey of [
        ["doctor", projectId],
        ["validation", projectId],
        ["items", projectId],
        ["tree-items", projectId],
        ["item", projectId],
        ["archived", projectId],
      ]) {
        void queryClient.invalidateQueries({ queryKey });
      }
    },
  });

  const fixes = plan.data?.fixes ?? [];
  const manual = plan.data?.manual ?? [];

  return (
    <Dialog.Root open onOpenChange={(open: boolean) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className={dialogStyles.overlay} />
        <Dialog.Content
          className={`${dialogStyles.content} ${styles.content}`}
          data-test-id="doctor-dialog"
        >
          <Dialog.Title className={dialogStyles.title}>Doctor</Dialog.Title>
          <Dialog.Description className={dialogStyles.description}>
            Safe fixes change only broken references and archive storage. Review
            the list before applying.
          </Dialog.Description>

          <div className={styles.body}>
            {plan.isLoading && <LoadingSpinner label="Checking project..." />}
            {plan.isError && (
              <div className={dialogStyles.error} role="alert">
                Failed to load diagnostics. Please try again.
              </div>
            )}
            {plan.data && (
              <>
                <section
                  className={styles.section}
                  aria-labelledby="doctor-safe-heading"
                  data-test-id="doctor-safe-fixes"
                >
                  <h3 id="doctor-safe-heading" className={styles.heading}>
                    Safe fixes ({fixes.length})
                  </h3>
                  {fixes.length === 0 ? (
                    <p className={styles.empty}>No automatic fixes available.</p>
                  ) : (
                    <ul className={styles.list}>
                      {fixes.map((fix) => (
                        <li
                          key={`${fix.path}|${fix.field ?? ""}|${fix.target ?? ""}|${fix.kind}`}
                          className={styles.row}
                        >
                          <span>{fix.description}</span>
                          <span className={styles.path}>{fix.path}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>

                <section
                  className={styles.section}
                  aria-labelledby="doctor-manual-heading"
                  data-test-id="doctor-manual-findings"
                >
                  <h3 id="doctor-manual-heading" className={styles.heading}>
                    Needs manual attention ({manual.length})
                  </h3>
                  {manual.length === 0 ? (
                    <p className={styles.empty}>Nothing else to fix.</p>
                  ) : (
                    <ul className={styles.list}>
                      {manual.map((finding, index) => (
                        <li
                          key={`${finding.path}|${finding.code}|${finding.field ?? ""}|${index}`}
                          className={styles.row}
                        >
                          <span>
                            <span
                              className={
                                finding.severity === "error"
                                  ? styles.severityError
                                  : styles.severityWarning
                              }
                            >
                              {finding.severity}
                            </span>{" "}
                            {finding.item_id && <strong>{finding.item_id}: </strong>}
                            {finding.message}
                          </span>
                          <span className={styles.path}>{finding.path}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </>
            )}
          </div>

          {apply.isSuccess && (
            <p
              className={styles.success}
              role="status"
              data-test-id="doctor-apply-result"
            >
              Applied {fixCount(apply.data.applied.length)}.
            </p>
          )}
          {apply.isSuccess && apply.data.failed.length > 0 && (
            <div
              className={dialogStyles.error}
              role="alert"
              data-test-id="doctor-apply-failures"
            >
              Could not apply {fixCount(apply.data.failed.length)}:
              <ul className={styles.failureList}>
                {apply.data.failed.map((failure) => (
                  <li key={`${failure.fix.path}|${failure.fix.field ?? ""}|${failure.fix.target ?? ""}`}>
                    {failure.fix.description}: {failure.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {apply.isError && (
            <div className={dialogStyles.error} role="alert">
              Failed to apply fixes: {apply.error.message}
            </div>
          )}

          <div className={dialogStyles.actions}>
            <Dialog.Close asChild>
              <button
                type="button"
                className={dialogStyles.cancelButton}
                data-test-id="doctor-close"
              >
                Close
              </button>
            </Dialog.Close>
            <button
              type="button"
              className={styles.applyButton}
              data-test-id="doctor-apply"
              disabled={fixes.length === 0 || apply.isPending || plan.isFetching}
              onClick={() => apply.mutate()}
            >
              {apply.isPending ? "Applying..." : `Apply ${fixCount(fixes.length)}`}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
