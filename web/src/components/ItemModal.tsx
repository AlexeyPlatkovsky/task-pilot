import { useState, useMemo, type ReactNode } from "react";
import {
  Bug,
  CheckSquare,
  Layers,
  Pencil,
  Trash2,
  X,
  Zap,
  type LucideIcon,
} from "lucide-react";
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

const TYPE_ICON_COMPONENTS: Record<ItemDetail["type"], LucideIcon> = {
  epic: Layers,
  feature: Zap,
  task: CheckSquare,
  bug: Bug,
};

const TYPE_SHORT_LABELS: Record<ItemDetail["type"], string> = {
  epic: "EPIC",
  feature: "FEAT",
  task: "TASK",
  bug: "BUG",
};

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
          <Dialog.Content
            className={styles.content}
            data-test-id={item ? `item-modal-${item.id}` : "item-modal"}
          >
            <Dialog.Title
              className={styles.title}
              data-test-id="item-modal-title"
              aria-label={
                item
                  ? `${TYPE_LABELS[item.type]} ${item.id} ${item.title}`
                  : itemId
                    ? `${itemId} Item Detail`
                    : undefined
              }
            >
              {item ? (
                <>
                  <TypeLabel type={item.type} />
                  <span className={styles.itemId} data-test-id="item-modal-id">
                    {item.id}
                  </span>
                  <span className={styles.itemTitle} data-test-id="item-modal-item-title">
                    {item.title}
                  </span>
                </>
              ) : itemId ? (
                <>
                  <span className={styles.itemId} data-test-id="item-modal-id">
                    {itemId}
                  </span>
                  <span className={styles.itemTitle} data-test-id="item-modal-item-title">
                    Item Detail
                  </span>
                </>
              ) : (
                "Item Detail"
              )}
            </Dialog.Title>
            <Dialog.Description className={styles.srOnly}>
              {isEditing ? "Edit item" : "Item detail view"}
            </Dialog.Description>

            <div className={styles.headerActions} data-test-id="item-modal-actions">
              {item && !isEditing && (
                <>
                  <button
                    type="button"
                    className={`${styles.iconButton} ${styles.editButton}`}
                    data-test-id="item-modal-edit"
                    onClick={() => setIsEditing(true)}
                    aria-label="Edit"
                  >
                    <Icon icon={Pencil} label="Edit" size={18} />
                  </button>
                  {item.status !== "deleted" && (
                    <button
                      type="button"
                      className={`${styles.iconButton} ${styles.deleteButton}`}
                      data-test-id="item-modal-delete"
                      onClick={() => setIsDeleting(true)}
                      aria-label="Delete"
                    >
                      <Icon icon={Trash2} label="Delete" size={18} />
                    </button>
                  )}
                </>
              )}
              <Dialog.Close
                className={`${styles.iconButton} ${styles.closeButton}`}
                data-test-id="item-modal-close"
              >
                <Icon icon={X} label="Close" size={20} />
              </Dialog.Close>
            </div>

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
              <ItemDetailView item={item} />
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
  const tags = item.tags ?? [];
  const attachments = item.attachments ?? [];
  const externalRefs = item.external_refs ?? [];
  const hasResources =
    tags.length > 0 || attachments.length > 0 || externalRefs.length > 0;

  return (
    <div className={styles.detail}>
      <section className={styles.summary} aria-label="Item summary">
        <dl className={styles.summaryColumn}>
          <SummaryField label="Priority">
            <span
              className={`${styles.badge} ${styles.priorityBadge} ${styles[`priority-${item.priority}`]}`}
            >
              {PRIORITY_LABELS[item.priority]}
            </span>
          </SummaryField>
          <SummaryField label="Status">
            <span
              className={`${styles.badge} ${styles.statusBadge} ${styles[`status-${item.status}`]}`}
            >
              {STATUS_LABELS[item.status]}
            </span>
          </SummaryField>
        </dl>
        <dl className={styles.summaryColumn}>
          <SummaryField label="Created">
            <time dateTime={item.created_at}>
              {new Date(item.created_at).toLocaleString()}
            </time>
          </SummaryField>
          <SummaryField label="Updated">
            <time dateTime={item.updated_at}>
              {new Date(item.updated_at).toLocaleString()}
            </time>
          </SummaryField>
        </dl>
      </section>

      <DetailSection title="Info">
        <InfoGroup title="Description">
          {descriptionHtml ? (
            <div
              className={styles.description}
              dangerouslySetInnerHTML={{ __html: descriptionHtml }}
            />
          ) : (
            <p className={styles.emptyState}>No description yet.</p>
          )}
        </InfoGroup>

        <InfoGroup title="Readiness">
          <div className={styles.splitGrid}>
            <Checklist title="Definition of Ready" items={item.dor ?? []} />
            <Checklist title="Definition of Done" items={item.dod ?? []} />
          </div>
        </InfoGroup>

        <InfoGroup title="Resources">
          {hasResources ? (
            <div className={styles.resourceGrid}>
              {tags.length > 0 && (
                <div className={styles.resourceGroup}>
                  <h6>Tags</h6>
                  <div className={styles.tags}>
                    {tags.map((tag) => (
                      <span key={tag} className={styles.tag}>
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {attachments.length > 0 && (
                <div className={styles.resourceGroup}>
                  <h6>Attachments</h6>
                  <ul className={styles.compactList}>
                    {attachments.map((attachment) => (
                      <li key={attachment}>{attachment}</li>
                    ))}
                  </ul>
                </div>
              )}
              {externalRefs.length > 0 && (
                <div className={styles.resourceGroup}>
                  <h6>Links</h6>
                  <ul className={styles.compactList}>
                    {externalRefs.map((ref) => (
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
            </div>
          ) : (
            <p className={styles.emptyState}>
              No tags, attachments, or links.
            </p>
          )}
        </InfoGroup>
      </DetailSection>

      <DetailSection title="Comments">
        <CommentThread comments={item.comments} />
      </DetailSection>

      {!item.valid && item.findings && item.findings.length > 0 && (
        <DetailSection title="Validation Issues">
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
        </DetailSection>
      )}
    </div>
  );
}

function TypeLabel({ type }: { type: ItemDetail["type"] }) {
  return (
    <span
      className={`${styles.typeBadge} ${styles[`type-${type}`]}`}
      data-test-id="item-modal-type"
      aria-label={`Type: ${TYPE_LABELS[type]}`}
    >
      <Icon icon={TYPE_ICON_COMPONENTS[type]} label={TYPE_LABELS[type]} />
      {TYPE_SHORT_LABELS[type]}
    </span>
  );
}

function SummaryField({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className={styles.summaryField}>
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function DetailSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className={styles.section}>
      <h4>{title}</h4>
      {children}
    </section>
  );
}

function InfoGroup({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className={styles.infoGroup}>
      <h5>{title}</h5>
      {children}
    </div>
  );
}

function Checklist({ title, items }: { title: string; items: string[] }) {
  return (
    <div className={styles.checklistGroup}>
      <h6>{title}</h6>
      {items.length > 0 ? (
        <ul className={styles.checklist}>
          {items.map((criterion) => (
            <li key={criterion}>{criterion}</li>
          ))}
        </ul>
      ) : (
        <p className={styles.emptyState}>No {title} items.</p>
      )}
    </div>
  );
}
