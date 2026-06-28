import { ProjectSelector } from "./components/ProjectSelector";
import { ProjectWorkspace } from "./components/ProjectWorkspace";
import { ValidationStatus } from "./components/ValidationStatus";
import { ThemeSwitcher } from "./components/ThemeSwitcher";
import { useState } from "react";

function App() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(
    null,
  );

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
            onSelect={setSelectedProjectId}
          />
        </div>
        <ValidationStatus projectId={selectedProjectId} />
        <div className="header-right">
          <ThemeSwitcher />
        </div>
      </header>
      <main>
        {selectedProjectId ? (
          <ProjectWorkspace key={selectedProjectId} projectId={selectedProjectId} />
        ) : (
          <div className="empty-state">Select a project to view tasks</div>
        )}
      </main>
    </div>
  );
}

export default App;
