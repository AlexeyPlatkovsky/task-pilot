import * as Dialog from "@radix-ui/react-dialog";
import { useQuery } from "@tanstack/react-query";
import { fetchItem } from "../api";
import type { ItemDetail, Status, Priority, ItemType } from "../types";
import { CommentThread } from "./CommentThread";
import styles from "./ItemModal.module.css";

interface Props {
  projectId: string;
  itemId: string | null;
  onClose: () => void;
  onEdit?: (itemId: string) => void;
  onDelete?: (itemId: string) => void;
}

const STATUS_LABELS: Record<Status, string> = {
  backlog: "Backlog",
  ready: "Ready",
  in_progress: "In Progress",
  done: "Done",
  cancelled: "Cancelled",
  deleted: "Deleted",
};

const PRIORITY_LABELS: Record<Priority, string> = {
  low: "Low",
  normal: "Normal",
  high: "High",
};

const TYPE_LABELS: Record<ItemType, string> = {
  epic: "Epic",
  feature: "Feature",
  task: "Task",
  bug: "Bug",
};

export function ItemModal({
  projectId,
  itemId,
  onClose,
  onEdit,
  onDelete,
}: Props) {
  const {
    data: item,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["item", projectId, itemId],
    queryFn: () => fetchItem(projectId, itemId!),
    enabled: !!itemId,
  });

  return (
    <Dialog.Root open={!!itemId} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className={styles.overlay} />
        <Dialog.Content className={styles.content}>
          <Dialog.Title className={styles.title}>
            {item ? `${item.id}: ${item.title}` : "Item Detail"}
          </Dialog.Title>
          <Dialog.Description className={styles.srOnly}>
            Item detail view
          </Dialog.Description>

          <Dialog.Close className={styles.closeButton} aria-label="Close">
            &times;
          </Dialog.Close>

          {isLoading && <div className={styles.loading}>Loading item...</div>}

          {error && (
            <div className={styles.error}>
              <p>Failed to load item</p>
            </div>
          )}

          {item && <ItemDetailView item={item} />}

          {item && (
            <div className={styles.actions}>
              {onEdit && (
                <button
                  type="button"
                  className={styles.editButton}
                  onClick={() => onEdit(item.id)}
                >
                  Edit
                </button>
              )}
              {onDelete && item.status !== "deleted" && (
                <button
                  type="button"
                  className={styles.deleteButton}
                  onClick={() => onDelete(item.id)}
                >
                  Delete
                </button>
              )}
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function ItemDetailView({ item }: { item: ItemDetail }) {
  return (
    <div className={styles.detail}>
      <div className={styles.badges}>
        <span className={`${styles.badge} ${styles.typeBadge}`}>
          {TYPE_LABELS[item.type]}
        </span>
        <span className={`${styles.badge} ${styles.statusBadge} ${styles[`status-${item.status}`]}`}>
          {STATUS_LABELS[item.status]}
        </span>
        <span className={`${styles.badge} ${styles.priorityBadge} ${styles[`priority-${item.priority}`]}`}>
          {PRIORITY_LABELS[item.priority]}
        </span>
      </div>

      {item.description && (
        <div className={styles.section}>
          <h4>Description</h4>
          <div className={styles.description}>{item.description}</div>
        </div>
      )}

      <div className={styles.section}>
        <h4>Details</h4>
        <dl className={styles.fields}>
          <dt>Created</dt>
          <dd>{new Date(item.created_at).toLocaleString()}</dd>
          <dt>Updated</dt>
          <dd>{new Date(item.updated_at).toLocaleString()}</dd>
          {item.parent_id && (
            <>
              <dt>Parent</dt>
              <dd>{item.parent_id}</dd>
            </>
          )}
          {item.created_by && (
            <>
              <dt>Created by</dt>
              <dd>{item.created_by}</dd>
            </>
          )}
          {item.performed_by && (
            <>
              <dt>Performed by</dt>
              <dd>{item.performed_by}</dd>
            </>
          )}
        </dl>
      </div>

      {item.tags && item.tags.length > 0 && (
        <div className={styles.section}>
          <h4>Tags</h4>
          <div className={styles.tags}>
            {item.tags.map((tag) => (
              <span key={tag} className={styles.tag}>
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {item.dor && item.dor.length > 0 && (
        <div className={styles.section}>
          <h4>Definition of Ready</h4>
          <ul className={styles.checklist}>
            {item.dor.map((criterion) => (
              <li key={criterion}>{criterion}</li>
            ))}
          </ul>
        </div>
      )}

      {item.dod && item.dod.length > 0 && (
        <div className={styles.section}>
          <h4>Definition of Done</h4>
          <ul className={styles.checklist}>
            {item.dod.map((criterion) => (
              <li key={criterion}>{criterion}</li>
            ))}
          </ul>
        </div>
      )}

      {item.links && (
        <div className={styles.section}>
          <h4>Links</h4>
          {item.links.blocks && item.links.blocks.length > 0 && (
            <div>
              <strong>Blocks:</strong> {item.links.blocks.join(", ")}
            </div>
          )}
          {item.links.relates_to && item.links.relates_to.length > 0 && (
            <div>
              <strong>Relates to:</strong> {item.links.relates_to.join(", ")}
            </div>
          )}
        </div>
      )}

      {item.attachments && item.attachments.length > 0 && (
        <div className={styles.section}>
          <h4>Attachments</h4>
          <ul>
            {item.attachments.map((attachment) => (
              <li key={attachment}>{attachment}</li>
            ))}
          </ul>
        </div>
      )}

      {item.external_refs && item.external_refs.length > 0 && (
        <div className={styles.section}>
          <h4>External References</h4>
          <ul>
            {item.external_refs.map((ref) => (
              <li key={ref}>
                {ref.startsWith("http") ? (
                  <a href={ref} target="_blank" rel="noopener noreferrer">
                    {ref}
                  </a>
                ) : (
                  ref
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className={styles.section}>
        <h4>Comments</h4>
        <CommentThread comments={item.comments} />
      </div>

      {!item.valid && item.findings && item.findings.length > 0 && (
        <div className={styles.section}>
          <h4>Validation Issues</h4>
          <ul className={styles.findings}>
            {item.findings.map((finding, index) => (
              <li
                key={index}
                className={
                  finding.severity === "error"
                    ? styles.findingError
                    : styles.findingWarning
                }
              >
                [{finding.severity}] {finding.message}
                {finding.field && ` (field: ${finding.field})`}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
