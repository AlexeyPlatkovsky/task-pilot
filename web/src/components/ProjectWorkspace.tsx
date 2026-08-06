import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchArchivedItems, fetchItems } from "../api";
import { ItemListView } from "./ItemListView";
import { ItemModal } from "./ItemModal";
import { ItemTreeView } from "./ItemTreeView";
import { KanbanBoard } from "./KanbanBoard";
import { ValidationPanel } from "./ValidationPanel";
import { ArchivedBoard } from "./ArchivedBoard";
import styles from "./ProjectWorkspace.module.css";

export type ViewMode = "board" | "list" | "tree" | "archived";

interface Props {
  projectId: string;
  activeView: ViewMode;
}

const VIEW_LABELS: Record<ViewMode, string> = {
  board: "Board",
  list: "List",
  tree: "Tree",
  archived: "Archived",
};

export function ViewTabs({
  activeView,
  onChange,
}: {
  activeView: ViewMode;
  onChange: (view: ViewMode) => void;
}) {
  const allViews: ViewMode[] = ["board", "list", "archived"];

  return (
    <div className={styles.tabs} role="tablist" aria-label="Workspace views">
      {allViews.map((view) => (
        <button
          key={view}
          role="tab"
          type="button"
          aria-selected={activeView === view}
          data-test-id={`workspace-tab-${view}`}
          className={activeView === view ? styles.activeTab : styles.tab}
          onClick={() => onChange(view)}
        >
          {VIEW_LABELS[view]}
        </button>
      ))}
    </div>
  );
}

export function ProjectWorkspace({ projectId, activeView }: Props) {
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

  const activeItemsQuery = useQuery({
    queryKey: ["items", projectId],
    queryFn: () => fetchItems(projectId),
    enabled: activeView !== "board" && activeView !== "archived",
  });
  const archivedTreeItemsQuery = useQuery({
    queryKey: ["tree-items", projectId],
    queryFn: () => fetchArchivedItems(projectId),
    enabled: activeView === "tree",
  });
  const items =
    activeView === "tree"
      ? [...(activeItemsQuery.data ?? []), ...(archivedTreeItemsQuery.data ?? [])]
      : activeItemsQuery.data;
  const isLoading =
    activeItemsQuery.isLoading ||
    (activeView === "tree" && archivedTreeItemsQuery.isLoading);
  const error =
    activeItemsQuery.error ??
    (activeView === "tree" ? archivedTreeItemsQuery.error : null);
  const refetch = () => {
    void activeItemsQuery.refetch();
    if (activeView === "tree") {
      void archivedTreeItemsQuery.refetch();
    }
  };

  const renderActiveView = () => {
    if (activeView === "board") {
      return <KanbanBoard projectId={projectId} />;
    }

    if (activeView === "archived") {
      return (
        <ArchivedBoard
          projectId={projectId}
        />
      );
    }

    if (isLoading) {
      return (
        <div className={styles.loading} data-test-id="workspace-loading">
          Loading items...
        </div>
      );
    }

    if (error) {
      return (
        <div
          className={styles.error}
          role="alert"
          data-test-id="workspace-error"
        >
          <span>Failed to load items</span>
          <button type="button" onClick={() => refetch()}>
            Retry
          </button>
        </div>
      );
    }

    if (activeView === "list") {
      return (
        <ItemListView
          key={projectId}
          items={items ?? []}
          onItemClick={setSelectedItemId}
        />
      );
    }

    return (
      <ItemTreeView
        key={projectId}
        items={items ?? []}
        onItemClick={setSelectedItemId}
      />
    );
  };

  return (
    <section className={styles.workspace}>
      <ValidationPanel projectId={projectId} onItemClick={setSelectedItemId} />
      {renderActiveView()}
      <ItemModal
        projectId={projectId}
        itemId={selectedItemId}
        archivedItemIds={archivedTreeItemsQuery.data?.map((item) => item.id)}
        onClose={() => setSelectedItemId(null)}
      />
    </section>
  );
}
