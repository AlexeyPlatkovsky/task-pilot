interface Props {
  projectId: string;
}

export function KanbanBoard({ projectId }: Props) {
  return (
    <div>
      <h2>Kanban Board for {projectId}</h2>
      <p>Board will be implemented in F004-T3</p>
    </div>
  );
}
