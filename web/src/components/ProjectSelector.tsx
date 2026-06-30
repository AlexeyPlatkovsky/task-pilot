import { useQuery } from "@tanstack/react-query";
import { fetchProjects } from "../api";
import { DropdownSelect, type DropdownOption } from "./DropdownSelect";
import type { ProjectSummary } from "../types";
import styles from "./ProjectSelector.module.css";

interface Props {
  selectedProjectId: string | null;
  onSelect: (projectId: string) => void;
  projects?: ProjectSummary[];
}

export function ProjectSelector({
  selectedProjectId,
  onSelect,
  projects: projectsProp,
}: Props) {
  const {
    data: fetchedProjects,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects,
    enabled: !projectsProp,
  });

  const projects = projectsProp ?? fetchedProjects;

  if (isLoading) {
    return (
      <div className={styles.selector} data-test-id="project-selector-loading">
        Loading projects...
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.selector} data-test-id="project-selector-error">
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
        <span className={styles.empty} data-test-id="project-selector-empty">
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
  const projectOptions: DropdownOption[] = [
    { value: "", label: "Select a project..." },
    ...sorted.map((project) => ({
      value: project.id,
      label: `${project.name} (${project.key})`,
    })),
  ];

  return (
    <div className={styles.selector}>
      <DropdownSelect
        id="project-selector"
        label="Project"
        dataTestId="project-selector"
        value={selectedProjectId ?? ""}
        options={projectOptions}
        size="project"
        onChange={(value) => {
          if (value) onSelect(value);
        }}
      />
    </div>
  );
}
