import { ProjectSelector } from "./components/ProjectSelector";
import { KanbanBoard } from "./components/KanbanBoard";
import { useState } from "react";

function App() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(
    null,
  );

  return (
    <div className="app">
      <header>
        <h1>TaskPilot</h1>
        <ProjectSelector
          selectedProjectId={selectedProjectId}
          onSelect={setSelectedProjectId}
        />
      </header>
      <main>
        {selectedProjectId ? (
          <KanbanBoard projectId={selectedProjectId} />
        ) : (
          <div>Select a project to view the Kanban board</div>
        )}
      </main>
    </div>
  );
}

export default App;
