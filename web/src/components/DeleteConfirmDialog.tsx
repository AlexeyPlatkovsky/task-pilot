import * as AlertDialog from "@radix-ui/react-alert-dialog";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateItem } from "../api";
import styles from "./DeleteConfirmDialog.module.css";

interface Props {
  projectId: string;
  itemId: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function DeleteConfirmDialog({
  projectId,
  itemId,
  onConfirm,
  onCancel,
}: Props) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => updateItem(projectId, itemId, { status: "deleted" }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["items", projectId] });
      void queryClient.invalidateQueries({
        queryKey: ["item", projectId, itemId],
      });
      onConfirm();
    },
  });

  return (
    <AlertDialog.Root open onOpenChange={(open: boolean) => !open && onCancel()}>
      <AlertDialog.Portal>
        <AlertDialog.Overlay className={styles.overlay} />
        <AlertDialog.Content
          className={styles.content}
          data-test-id="delete-confirm-dialog"
        >
          <AlertDialog.Title className={styles.title}>
            Delete this item?
          </AlertDialog.Title>
          <AlertDialog.Description className={styles.description}>
            This will set the item status to &quot;deleted&quot;. The item will
            be hidden from the Kanban board but can still be accessed via direct
            lookup.
          </AlertDialog.Description>

          {mutation.isError && (
            <div className={styles.error}>
              Failed to delete item. Please try again.
            </div>
          )}

          <div className={styles.actions}>
            <AlertDialog.Cancel asChild>
              <button
                type="button"
                className={styles.cancelButton}
                data-test-id="delete-confirm-cancel"
                disabled={mutation.isPending}
                onClick={onCancel}
              >
                Cancel
              </button>
            </AlertDialog.Cancel>
            <AlertDialog.Action asChild>
              <button
                type="button"
                className={styles.deleteButton}
                data-test-id="delete-confirm-submit"
                disabled={mutation.isPending}
                onClick={() => mutation.mutate()}
              >
                {mutation.isPending ? "Deleting..." : "Delete"}
              </button>
            </AlertDialog.Action>
          </div>
        </AlertDialog.Content>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  );
}
