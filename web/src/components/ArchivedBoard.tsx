import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, useCallback } from "react";
import { fetchArchivedItems, unarchiveItem } from "../api";
import type { ItemSummary } from "../types";
import { PRIORITY_LABELS, STATUS_LABELS, TYPE_LABELS } from "../types/labels";
import { ItemModal } from "./ItemModal";
import { LoadingSpinner } from "./ui/LoadingSpinner";
import { UnarchiveConfirmDialog } from "./UnarchiveConfirmDialog";
import styles from "./ArchivedBoard.module.css";

interface Props {
  projectId: string;
}

const ARCHIVE_TYPE_ORDER: Record<ItemSummary["type"], number> = {
  epic: 0,
  feature: 1,
  task: 2,
  bug: 3,
};

function numericIdKey(item: ItemSummary): [number, string] {
  const suffix = item.id.split("-").pop();
  const numericId = suffix ? Number.parseInt(suffix, 10) : Number.NaN;
  return [Number.isNaN(numericId) ? -1 : numericId, item.id];
}

function sortArchivedItems(items: ItemSummary[]): ItemSummary[] {
  return [...items].sort((left, right) => {
    const typeOrder = ARCHIVE_TYPE_ORDER[left.type] - ARCHIVE_TYPE_ORDER[right.type];
    if (typeOrder !== 0) return typeOrder;
    const [leftNumber, leftId] = numericIdKey(left);
    const [rightNumber, rightId] = numericIdKey(right);
    return leftNumber - rightNumber || leftId.localeCompare(rightId);
  });
}

export function ArchivedBoard({ projectId }: Props) {
  const queryClient = useQueryClient();
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [pendingUnarchive, setPendingUnarchive] = useState<string | null>(null);
  const [unarchiveError, setUnarchiveError] = useState<string | null>(null);
  const [isUnarchiving, setIsUnarchiving] = useState(false);

  const {
    data: items,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["archived", projectId],
    queryFn: () => fetchArchivedItems(projectId),
  });

  const handleUnarchive = useCallback(
    (itemId: string) => {
      setIsUnarchiving(true);
      setUnarchiveError(null);
      void unarchiveItem(projectId, itemId).then(() => {
        void refetch();
        void queryClient.invalidateQueries({ queryKey: ["items", projectId] });
        setPendingUnarchive(null);
      }).catch((error: unknown) => {
        setUnarchiveError(error instanceof Error ? error.message : "Could not unarchive item");
      }).finally(() => setIsUnarchiving(false));
    },
    [projectId, queryClient, refetch],
  );

  const archivedItems = sortArchivedItems(items ?? []);
  const hasItems = archivedItems.length > 0;
  const showEmptyPrompt = !hasItems;

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <LoadingSpinner label="Loading archived items..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.error} role="alert">
        <p>Failed to load archived items</p>
        <button type="button" onClick={() => refetch()}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <>
      <div className={styles.listFrame} data-test-id="archived-list">
        {hasItems && (
          <ul className={styles.list} aria-label="Archived items">
            {archivedItems.map((item) => (
              <li
                key={item.id}
                className={styles.row}
                data-test-id="archived-list-row"
                data-item-id={item.id}
              >
                <button
                  type="button"
                  className={styles.openButton}
                  data-test-id={`archived-list-open-${item.id}`}
                  onClick={() => setSelectedItemId(item.id)}
                  disabled={!item.valid}
                  aria-label={`Open ${item.id}`}
                >
                  <span className={styles.id}>{item.id}</span>
                  <span className={`${styles.type} ${styles[`type-${item.type}`]}`}>
                    {TYPE_LABELS[item.type]}
                  </span>
                  <span className={styles.title}>{item.title}</span>
                  <span className={styles.metadata}>
                    {STATUS_LABELS[item.status]} · {PRIORITY_LABELS[item.priority]}
                  </span>
                </button>
                <button
                  type="button"
                  className={styles.unarchiveButton}
                  data-test-id={`unarchive-button-${item.id}`}
                  onClick={() => setPendingUnarchive(item.id)}
                >
                  Unarchive
                </button>
              </li>
            ))}
          </ul>
        )}
        {showEmptyPrompt && (
          <div className={styles.emptyPrompt} data-test-id="archived-empty-prompt">
            <p>No archived items.</p>
          </div>
        )}
      </div>

      <ItemModal
        projectId={projectId}
        itemId={selectedItemId}
        onClose={() => setSelectedItemId(null)}
        readOnly
      />
      {pendingUnarchive && (
        <UnarchiveConfirmDialog itemId={pendingUnarchive} onConfirm={() => handleUnarchive(pendingUnarchive)} onCancel={() => { setPendingUnarchive(null); setUnarchiveError(null); }} pending={isUnarchiving} error={unarchiveError} />
      )}
    </>
  );
}
