import { ProjectSelector } from "./components/ProjectSelector";
import { ProjectWorkspace } from "./components/ProjectWorkspace";
import { useState } from "react";

function App() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(
    null,
  );

  return (
    <div className="app">
      <header>
        <img
          className="logo"
          src="/task-pilot-compass-board.svg"
          alt="TaskPilot"
          width={32}
          height={32}
        />
        <h1>TaskPilot</h1>
        <ProjectSelector
          selectedProjectId={selectedProjectId}
          onSelect={setSelectedProjectId}
        />
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
