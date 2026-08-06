import * as AlertDialog from "@radix-ui/react-alert-dialog";
import styles from "./DeleteConfirmDialog.module.css";

interface Props {
  itemId: string;
  onConfirm: () => void;
  onCancel: () => void;
  pending?: boolean;
  error?: string | null;
}

export function UnarchiveConfirmDialog({ itemId, onConfirm, onCancel, pending = false, error }: Props) {
  return (
    <AlertDialog.Root open onOpenChange={(open) => !open && onCancel()}>
      <AlertDialog.Portal>
        <AlertDialog.Overlay className={styles.overlay} />
        <AlertDialog.Content className={styles.content} data-test-id="unarchive-confirm-dialog">
          <AlertDialog.Title className={styles.title}>Unarchive {itemId}?</AlertDialog.Title>
          <AlertDialog.Description className={styles.description}>
            This item will return to the active workspace with its original status.
          </AlertDialog.Description>
          {error && <p className={styles.error} role="alert">{error}</p>}
          <div className={styles.actions}>
            <AlertDialog.Cancel asChild><button type="button" className={styles.cancelButton} onClick={onCancel} disabled={pending}>Cancel</button></AlertDialog.Cancel>
            <button type="button" className={styles.confirmButton} data-test-id="unarchive-confirm-submit" onClick={onConfirm} disabled={pending}>{pending ? "Unarchiving…" : "Unarchive"}</button>
          </div>
        </AlertDialog.Content>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  );
}
