import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import { useMemo } from "react";
import type { ItemSummary } from "../types";
import {
  PRIORITY_LABELS,
  STATUS_LABELS,
  TYPE_LABELS,
} from "../types/labels";
import styles from "./ItemListView.module.css";

interface Props {
  items: ItemSummary[];
  onItemClick: (itemId: string) => void;
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "n/a";
  }
  return value;
}

function labelFor(
  labels: Record<string, string>,
  value: string | null | undefined,
): string {
  if (!value) {
    return "Unknown";
  }
  return labels[value] ?? value;
}

export function ItemListView({ items, onItemClick }: Props) {
  const columns = useMemo<ColumnDef<ItemSummary>[]>(
    () => [
      {
        accessorKey: "id",
        header: "ID",
        cell: ({ row }) => (
          <span className={styles.idCell}>{row.original.id}</span>
        ),
      },
      {
        accessorKey: "title",
        header: "Title",
        cell: ({ row }) => (
          <button
            className={styles.titleButton}
            type="button"
            onClick={() => onItemClick(row.original.id)}
            disabled={!row.original.valid}
            aria-label={`Open ${row.original.id}`}
          >
            {row.original.title}
          </button>
        ),
      },
      {
        accessorKey: "type",
        header: "Type",
        cell: ({ row }) => labelFor(TYPE_LABELS, row.original.type),
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => labelFor(STATUS_LABELS, row.original.status),
      },
      {
        accessorKey: "priority",
        header: "Priority",
        cell: ({ row }) => labelFor(PRIORITY_LABELS, row.original.priority),
      },
      {
        accessorKey: "created_at",
        header: "Created",
        cell: ({ row }) => formatDate(row.original.created_at),
      },
      {
        accessorKey: "updated_at",
        header: "Updated",
        cell: ({ row }) => formatDate(row.original.updated_at),
      },
    ],
    [onItemClick],
  );

  const table = useReactTable({
    data: items,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (items.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No items yet.</p>
        <p>
          Create your first item with: <code>taskpilot item create</code>
        </p>
      </div>
    );
  }

  return (
    <div className={styles.tableFrame}>
      <table className={styles.table}>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} scope="col">
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} data-item-id={row.original.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
