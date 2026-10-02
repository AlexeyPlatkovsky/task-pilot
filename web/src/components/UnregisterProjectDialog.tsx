import * as AlertDialog from "@radix-ui/react-alert-dialog";
import { useMutation } from "@tanstack/react-query";
import { unregisterProject } from "../api";
import type { ProjectSummary } from "../types";
import styles from "./DeleteConfirmDialog.module.css";

interface Props {
  project: ProjectSummary;
  onUnregistered: (projectId: string) => void;
  onCancel: () => void;
}

export function UnregisterProjectDialog({ project, onUnregistered, onCancel }: Props) {
  const mutation = useMutation({
    mutationFn: () => unregisterProject(project.id),
    onSuccess: () => onUnregistered(project.id),
  });

  return (
    <AlertDialog.Root
      open
      onOpenChange={(open: boolean) => {
        // Keep the dialog open while the request runs so a failure can still be shown.
        if (!open && !mutation.isPending) onCancel();
      }}
    >
      <AlertDialog.Portal>
        <AlertDialog.Overlay className={styles.overlay} />
        <AlertDialog.Content
          className={styles.content}
          data-test-id="unregister-project-dialog"
        >
          <AlertDialog.Title className={styles.title}>
            Unregister {project.name}?
          </AlertDialog.Title>
          <AlertDialog.Description className={styles.description}>
            The project is removed from this machine&apos;s TaskPilot list. Its{" "}
            <code>.taskpilot/</code> files on disk are kept and can be registered
            again with <code>taskpilot init</code>.
          </AlertDialog.Description>

          {mutation.isError && (
            <div className={styles.error} role="alert">
              Failed to unregister project. Please try again.
            </div>
          )}

          <div className={styles.actions}>
            <AlertDialog.Cancel asChild>
              <button
                type="button"
                className={styles.cancelButton}
                data-test-id="unregister-project-cancel"
                disabled={mutation.isPending}
              >
                Cancel
              </button>
            </AlertDialog.Cancel>
            <button
              type="button"
              className={styles.deleteButton}
              data-test-id="unregister-project-submit"
              disabled={mutation.isPending}
              onClick={() => mutation.mutate()}
            >
              {mutation.isPending ? "Unregistering..." : "Unregister"}
            </button>
          </div>
        </AlertDialog.Content>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  );
}
