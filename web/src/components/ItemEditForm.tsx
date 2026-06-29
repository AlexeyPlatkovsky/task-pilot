import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateItem } from "../api";
import type { ItemDetail, EditableStatus } from "../types";
import { EDITABLE_STATUSES, PRIORITIES } from "../types";
import { STATUS_LABELS, PRIORITY_LABELS } from "../types/labels";
import styles from "./ItemEditForm.module.css";

const itemEditSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title is too long"),
  description: z.string().optional(),
  priority: z.enum(PRIORITIES),
  status: z.enum(EDITABLE_STATUSES),
});

type ItemEditFormData = z.infer<typeof itemEditSchema>;

interface Props {
  projectId: string;
  item: ItemDetail;
  onSave: () => void;
  onCancel: () => void;
}

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
      status:
        item.status === "deleted"
          ? ("backlog" as EditableStatus)
          : (item.status as EditableStatus),
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
    <form
      className={styles.form}
      data-test-id="item-edit-form"
      onSubmit={handleSubmit(onSubmit)}
    >
      <div className={styles.field}>
        <label className={styles.label} htmlFor="title">
          Title
        </label>
        <input
          id="title"
          className={styles.input}
          data-test-id="item-edit-title"
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
          data-test-id="item-edit-description"
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
            data-test-id="item-edit-priority"
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
            data-test-id="item-edit-status"
            {...register("status")}
          >
            {EDITABLE_STATUSES.map((s) => (
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
          data-test-id="item-edit-cancel"
          onClick={onCancel}
          disabled={mutation.isPending}
        >
          Cancel
        </button>
        <button
          type="submit"
          className={styles.saveButton}
          data-test-id="item-edit-save"
          disabled={!isDirty || mutation.isPending}
        >
          {mutation.isPending ? "Saving..." : "Save"}
        </button>
      </div>
    </form>
  );
}
