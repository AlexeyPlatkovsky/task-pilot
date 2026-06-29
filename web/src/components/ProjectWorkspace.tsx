import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchItems } from "../api";
import { ItemListView } from "./ItemListView";
import { ItemModal } from "./ItemModal";
import { ItemTreeView } from "./ItemTreeView";
import { KanbanBoard } from "./KanbanBoard";
import { ValidationPanel } from "./ValidationPanel";
import styles from "./ProjectWorkspace.module.css";

export type ViewMode = "board" | "list" | "tree";

interface Props {
  projectId: string;
  activeView: ViewMode;
}

const VIEW_LABELS: Record<ViewMode, string> = {
  board: "Board",
  list: "List",
  tree: "Tree",
};

export function ViewTabs({
  activeView,
  onChange,
}: {
  activeView: ViewMode;
  onChange: (view: ViewMode) => void;
}) {
  return (
    <div className={styles.tabs} role="tablist" aria-label="Workspace views">
      {(["board", "list", "tree"] as const).map((view) => (
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

  const {
    data: items,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["items", projectId],
    queryFn: () => fetchItems(projectId),
    enabled: activeView !== "board",
  });

  const renderActiveView = () => {
    if (activeView === "board") {
      return <KanbanBoard projectId={projectId} />;
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
        onClose={() => setSelectedItemId(null)}
      />
    </section>
  );
}
