import { ProjectSelector } from "./components/ProjectSelector";
import {
  ProjectWorkspace,
  ViewTabs,
  type ViewMode,
} from "./components/ProjectWorkspace";
import { ValidationStatus } from "./components/ValidationStatus";
import { ThemeSwitcher } from "./components/ThemeSwitcher";
import { useState, useEffect, useCallback } from "react";
import { fetchUIState, fetchProjects, patchUIState } from "./api";
import type { ProjectSummary } from "./types";

function App() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(
    null,
  );
  const [activeView, setActiveView] = useState<ViewMode>("board");
  const [startupDone, setStartupDone] = useState(false);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function restore() {
      try {
        const [state, projList] = await Promise.all([
          fetchUIState().catch(() => null),
          fetchProjects().catch(() => []),
        ]);
        if (cancelled) return;

        setProjects(projList);

        if (state?.last_opened_project_id) {
          const remembered = projList.find(
            (p) =>
              p.id === state.last_opened_project_id && p.active,
          );
          if (remembered) {
            setSelectedProjectId(remembered.id);
          }
        }
      } catch {
        // fall through to startup done
      } finally {
        if (!cancelled) setStartupDone(true);
      }
    }

    restore();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleProjectSelect = useCallback(
    (projectId: string) => {
      setSelectedProjectId(projectId);
      patchUIState(projectId).catch(() => {
        // keep current session usable even if save fails
      });
    },
    [],
  );

  if (!startupDone) {
    return (
      <div className="app">
        <header>
          <div className="header-left">
            <img
              className="logo"
              src="/task-pilot-compass-board.svg"
              alt="TaskPilot"
              width={32}
              height={32}
            />
            <h1 data-test-id="app-title">TaskPilot</h1>
            <div data-test-id="project-selector-loading">
              Loading...
            </div>
          </div>
          <div className="header-right">
            <ThemeSwitcher />
          </div>
        </header>
        <main>
          <div className="empty-state">Loading...</div>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <header>
        <div className="header-left">
          <img
            className="logo"
            src="/task-pilot-compass-board.svg"
            alt="TaskPilot"
            width={32}
            height={32}
          />
          <h1 data-test-id="app-title">TaskPilot</h1>
          <ProjectSelector
            selectedProjectId={selectedProjectId}
            onSelect={handleProjectSelect}
            projects={projects}
          />
          {selectedProjectId && (
            <ViewTabs activeView={activeView} onChange={setActiveView} />
          )}
        </div>
        <ValidationStatus projectId={selectedProjectId} />
        <div className="header-right">
          <ThemeSwitcher />
        </div>
      </header>
      <main>
        {selectedProjectId ? (
          <ProjectWorkspace
            key={selectedProjectId}
            projectId={selectedProjectId}
            activeView={activeView}
          />
        ) : (
          <div className="empty-state">Select a project to view tasks</div>
        )}
      </main>
    </div>
  );
}

export default App;
