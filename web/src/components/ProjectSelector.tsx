import { useQuery } from "@tanstack/react-query";
import { fetchProjects } from "../api";
import styles from "./ProjectSelector.module.css";

interface Props {
  selectedProjectId: string | null;
  onSelect: (projectId: string) => void;
}

export function ProjectSelector({ selectedProjectId, onSelect }: Props) {
  const {
    data: projects,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });

  if (isLoading) {
    return <div className={styles.selector}>Loading projects...</div>;
  }

  if (error) {
    return (
      <div className={styles.selector}>
        <span className={styles.error}>Failed to load projects</span>
        <button type="button" onClick={() => refetch()}>
          Retry
        </button>
      </div>
    );
  }

  if (!projects || projects.length === 0) {
    return (
      <div className={styles.selector}>
        <span className={styles.empty}>
          No projects registered. Run <code>taskpilot init .</code> to
          register a project.
        </span>
      </div>
    );
  }

  const activeProjects = projects.filter((p) => p.active);
  const sorted = [...activeProjects].sort((a, b) =>
    a.name.localeCompare(b.name),
  );

  return (
    <div className={styles.selector}>
      <select
        className={styles.select}
        value={selectedProjectId ?? ""}
        onChange={(e) => {
          const value = e.target.value;
          if (value) onSelect(value);
        }}
      >
        <option value="">Select a project...</option>
        {sorted.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name} ({project.key})
          </option>
        ))}
      </select>
    </div>
  );
}
