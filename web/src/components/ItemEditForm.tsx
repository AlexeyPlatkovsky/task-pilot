import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateItem } from "../api";
import type { ItemDetail, Priority, Status } from "../types";
import { STATUSES, PRIORITIES } from "../types";
import styles from "./ItemEditForm.module.css";

const itemEditSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title is too long"),
  description: z.string().optional(),
  priority: z.enum(PRIORITIES),
  status: z.enum(STATUSES),
});

type ItemEditFormData = z.infer<typeof itemEditSchema>;

interface Props {
  projectId: string;
  item: ItemDetail;
  onSave: () => void;
  onCancel: () => void;
}

const STATUS_LABELS: Record<Status, string> = {
  backlog: "Backlog",
  ready: "Ready",
  in_progress: "In Progress",
  done: "Done",
  cancelled: "Cancelled",
  deleted: "Deleted",
};

const PRIORITY_LABELS: Record<Priority, string> = {
  low: "Low",
  normal: "Normal",
  high: "High",
};

export function ItemEditForm({
  projectId,
  item,
  onSave,
  onCancel,
}: Props) {
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<ItemEditFormData>({
    resolver: zodResolver(itemEditSchema),
    defaultValues: {
      title: item.title,
      description: item.description ?? "",
      priority: item.priority,
      status: item.status,
    },
  });

  const mutation = useMutation({
    mutationFn: (data: ItemEditFormData) =>
      updateItem(projectId, item.id, {
        title: data.title,
        description: data.description || undefined,
        priority: data.priority,
        status: data.status,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["items", projectId] });
      void queryClient.invalidateQueries({
        queryKey: ["item", projectId, item.id],
      });
      onSave();
    },
  });

  const onSubmit = (data: ItemEditFormData) => {
    mutation.mutate(data);
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit(onSubmit)}>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="title">
          Title
        </label>
        <input
          id="title"
          className={styles.input}
          {...register("title")}
          aria-invalid={!!errors.title}
        />
        {errors.title && (
          <span className={styles.error}>{errors.title.message}</span>
        )}
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor="description">
          Description
        </label>
        <textarea
          id="description"
          className={styles.textarea}
          rows={6}
          {...register("description")}
        />
      </div>

      <div className={styles.row}>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="priority">
            Priority
          </label>
          <select
            id="priority"
            className={styles.select}
            {...register("priority")}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {PRIORITY_LABELS[p]}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="status">
            Status
          </label>
          <select
            id="status"
            className={styles.select}
            {...register("status")}
          >
            {STATUSES.filter((s) => s !== "deleted").map((s) => (
              <option key={s} value={s}>
                {STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </div>
      </div>

      {mutation.isError && (
        <div className={styles.mutationError}>
          Failed to save changes. Please try again.
        </div>
      )}

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.cancelButton}
          onClick={onCancel}
          disabled={mutation.isPending}
        >
          Cancel
        </button>
        <button
          type="submit"
          className={styles.saveButton}
          disabled={!isDirty || mutation.isPending}
        >
          {mutation.isPending ? "Saving..." : "Save"}
        </button>
      </div>
    </form>
  );
}
