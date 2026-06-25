interface Props {
  selectedProjectId: string | null;
  onSelect: (projectId: string) => void;
}

export function ProjectSelector({ selectedProjectId, onSelect }: Props) {
  return (
    <div>
      <select
        value={selectedProjectId ?? ""}
        onChange={(e) => onSelect(e.target.value)}
      >
        <option value="">Select a project...</option>
      </select>
    </div>
  );
}
