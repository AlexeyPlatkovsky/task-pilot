import { useState, useMemo } from "react";
import { X } from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";
import { useQuery } from "@tanstack/react-query";
import { marked } from "marked";
import DOMPurify from "dompurify";
import { fetchItem } from "../api";
import type { ItemDetail } from "../types";
import { STATUS_LABELS, PRIORITY_LABELS, TYPE_LABELS } from "../types/labels";
import { Icon } from "./ui/Icon";
import { CommentThread } from "./CommentThread";
import { ItemEditForm } from "./ItemEditForm";
import { DeleteConfirmDialog } from "./DeleteConfirmDialog";
import styles from "./ItemModal.module.css";

interface Props {
  projectId: string;
  itemId: string | null;
  onClose: () => void;
}

export function ItemModal({ projectId, itemId, onClose }: Props) {
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const {
    data: item,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["item", projectId, itemId],
    queryFn: () => fetchItem(projectId, itemId!),
    enabled: !!itemId,
  });

  const handleClose = () => {
    setIsEditing(false);
    setIsDeleting(false);
    onClose();
  };

  const handleSave = () => {
    setIsEditing(false);
  };

  const handleDeleteConfirm = () => {
    setIsDeleting(false);
    handleClose();
  };

  return (
    <>
      <Dialog.Root
        open={!!itemId && !isDeleting}
        onOpenChange={(open) => !open && handleClose()}
      >
        <Dialog.Portal>
          <Dialog.Overlay className={styles.overlay} />
          <Dialog.Content className={styles.content}>
            <Dialog.Title className={styles.title}>
              {item ? `${item.id}: ${item.title}` : "Item Detail"}
            </Dialog.Title>
            <Dialog.Description className={styles.srOnly}>
              {isEditing ? "Edit item" : "Item detail view"}
            </Dialog.Description>

            <Dialog.Close className={styles.closeButton}>
              <Icon icon={X} label="Close" size={20} />
            </Dialog.Close>

            {isLoading && <div className={styles.loading}>Loading item...</div>}

            {error && (
              <div className={styles.error}>
                <p>Failed to load item</p>
                <button
                  type="button"
                  className={styles.retryButton}
                  onClick={() => refetch()}
                >
                  Retry
                </button>
              </div>
            )}

            {item && isEditing && (
              <ItemEditForm
                projectId={projectId}
                item={item}
                onSave={handleSave}
                onCancel={() => setIsEditing(false)}
              />
            )}

            {item && !isEditing && (
              <>
                <ItemDetailView item={item} />
                <div className={styles.actions}>
                  <button
                    type="button"
                    className={styles.editButton}
                    onClick={() => setIsEditing(true)}
                  >
                    Edit
                  </button>
                  {item.status !== "deleted" && (
                    <button
                      type="button"
                      className={styles.deleteButton}
                      onClick={() => setIsDeleting(true)}
                    >
                      Delete
                    </button>
                  )}
                </div>
              </>
            )}
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {itemId && isDeleting && (
        <DeleteConfirmDialog
          projectId={projectId}
          itemId={itemId}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setIsDeleting(false)}
        />
      )}
    </>
  );
}

function ItemDetailView({ item }: { item: ItemDetail }) {
  const descriptionHtml = useMemo(
    () =>
      item.description
        ? DOMPurify.sanitize(marked.parse(item.description) as string)
        : null,
    [item.description],
  );

  return (
    <div className={styles.detail}>
      <div className={styles.badges}>
        <span className={`${styles.badge} ${styles.typeBadge}`}>
          {TYPE_LABELS[item.type]}
        </span>
        <span
          className={`${styles.badge} ${styles.statusBadge} ${styles[`status-${item.status}`]}`}
        >
          {STATUS_LABELS[item.status]}
        </span>
        <span
          className={`${styles.badge} ${styles.priorityBadge} ${styles[`priority-${item.priority}`]}`}
        >
          {PRIORITY_LABELS[item.priority]}
        </span>
      </div>

      {descriptionHtml && (
        <div className={styles.section}>
          <h4>Description</h4>
          <div
            className={styles.description}
            dangerouslySetInnerHTML={{ __html: descriptionHtml }}
          />
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
