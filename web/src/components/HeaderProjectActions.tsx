import { useRef, useState } from "react";
import { Stethoscope, Trash2 } from "lucide-react";
import type { ProjectSummary } from "../types";
import { DoctorDialog } from "./DoctorDialog";
import { UnregisterProjectDialog } from "./UnregisterProjectDialog";
import styles from "./HeaderProjectActions.module.css";

interface Props {
  project: ProjectSummary;
  onUnregistered: (projectId: string) => void;
}

type OpenDialog = "doctor" | "unregister" | null;

export function HeaderProjectActions({ project, onUnregistered }: Props) {
  const [open, setOpen] = useState<OpenDialog>(null);
  const doctorButton = useRef<HTMLButtonElement>(null);
  const unregisterButton = useRef<HTMLButtonElement>(null);

  function close(trigger: React.RefObject<HTMLButtonElement | null>) {
    setOpen(null);
    // The dialogs are controlled without a Radix trigger, so restore focus here.
    window.setTimeout(() => trigger.current?.focus(), 0);
  }

  return (
    <>
      <button
        ref={doctorButton}
        type="button"
        className={styles.iconButton}
        aria-label="Doctor"
        title="Doctor"
        data-test-id="header-doctor-button"
        onClick={() => setOpen("doctor")}
      >
        <Stethoscope size={16} aria-hidden="true" />
      </button>
      <button
        ref={unregisterButton}
        type="button"
        className={`${styles.iconButton} ${styles.destructive}`}
        aria-label="Unregister project"
        title="Unregister project"
        data-test-id="header-unregister-button"
        onClick={() => setOpen("unregister")}
      >
        <Trash2 size={16} aria-hidden="true" />
      </button>

      {open === "doctor" && (
        <DoctorDialog projectId={project.id} onClose={() => close(doctorButton)} />
      )}
      {open === "unregister" && (
        <UnregisterProjectDialog
          project={project}
          onCancel={() => close(unregisterButton)}
          onUnregistered={(projectId) => {
            setOpen(null);
            onUnregistered(projectId);
          }}
        />
      )}
    </>
  );
}
