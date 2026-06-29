import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { useMemo, useState } from "react";
import type { ItemSummary } from "../types";
import { ITEM_TYPES, PRIORITIES, WORKFLOW_STATUSES } from "../types";
import {
  PRIORITY_LABELS,
  STATUS_LABELS,
  TYPE_LABELS,
} from "../types/labels";
import styles from "./ItemListView.module.css";

interface Props {
  items: ItemSummary[];
  onItemClick: (itemId: string) => void;
  now?: Date;
}

type TimeRange = "all" | "last_7_days" | "last_14_days" | "last_30_days";

interface Filters {
  status: string;
  type: string;
  priority: string;
  timeRange: TimeRange;
}

const TIME_RANGE_DAYS: Record<Exclude<TimeRange, "all">, number> = {
  last_7_days: 7,
  last_14_days: 14,
  last_30_days: 30,
};

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

function isWithinTimeRange(
  item: ItemSummary,
  timeRange: TimeRange,
  now: Date,
): boolean {
  if (timeRange === "all") {
    return true;
  }
  if (!item.updated_at) {
    return false;
  }
  const updated = new Date(item.updated_at);
  if (Number.isNaN(updated.getTime())) {
    return false;
  }
  const days = TIME_RANGE_DAYS[timeRange];
  const earliest = now.getTime() - days * 24 * 60 * 60 * 1000;
  return updated.getTime() >= earliest && updated.getTime() <= now.getTime();
}

function sortStateLabel(sortState: false | "asc" | "desc"): string {
  if (sortState === "asc") {
    return "ascending";
  }
  if (sortState === "desc") {
    return "descending";
  }
  return "not sorted";
}

function sortAriaValue(
  sortState: false | "asc" | "desc",
): "ascending" | "descending" | "none" {
  if (sortState === "asc") {
    return "ascending";
  }
  if (sortState === "desc") {
    return "descending";
  }
  return "none";
}

export function ItemListView({
  items,
  onItemClick,
  now,
}: Props) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [defaultNow] = useState(() => new Date());
  const [filters, setFilters] = useState<Filters>({
    status: "",
    type: "",
    priority: "",
    timeRange: "all",
  });
  const filterNow = now ?? defaultNow;

  const filteredItems = useMemo(
    () =>
      items.filter((item) => {
        if (filters.status && item.status !== filters.status) {
          return false;
        }
        if (filters.type && item.type !== filters.type) {
          return false;
        }
        if (filters.priority && item.priority !== filters.priority) {
          return false;
        }
        return isWithinTimeRange(item, filters.timeRange, filterNow);
      }),
    [filters, items, filterNow],
  );

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
            data-test-id={`item-list-open-${row.original.id}`}
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
    data: filteredItems,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    enableSortingRemoval: false,
  });

  if (items.length === 0) {
    return (
      <div className={styles.emptyState} data-test-id="item-list-empty">
        <p>No items yet.</p>
        <p>
          Create your first item with: <code>taskpilot item create</code>
        </p>
      </div>
    );
  }

  return (
    <>
      <div
        className={styles.filterBar}
        aria-label="List filters"
        data-test-id="item-list-filters"
      >
        <label>
          <span>Status</span>
          <select
            data-test-id="item-list-filter-status"
            value={filters.status}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                status: event.target.value,
              }))
            }
          >
            <option value="">All statuses</option>
            {WORKFLOW_STATUSES.map((status) => (
              <option key={status} value={status}>
                {STATUS_LABELS[status]}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Type</span>
          <select
            data-test-id="item-list-filter-type"
            value={filters.type}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                type: event.target.value,
              }))
            }
          >
            <option value="">All types</option>
            {ITEM_TYPES.map((type) => (
              <option key={type} value={type}>
                {TYPE_LABELS[type]}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Priority</span>
          <select
            data-test-id="item-list-filter-priority"
            value={filters.priority}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                priority: event.target.value,
              }))
            }
          >
            <option value="">All priorities</option>
            {PRIORITIES.map((priority) => (
              <option key={priority} value={priority}>
                {PRIORITY_LABELS[priority]}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Updated</span>
          <select
            data-test-id="item-list-filter-updated"
            value={filters.timeRange}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                timeRange: event.target.value as TimeRange,
              }))
            }
          >
            <option value="all">Any time</option>
            <option value="last_7_days">Last 7 days</option>
            <option value="last_14_days">Last 14 days</option>
            <option value="last_30_days">Last 30 days</option>
          </select>
        </label>
      </div>

      {filteredItems.length === 0 ? (
        <div
          className={styles.filteredEmptyState}
          data-test-id="item-list-filtered-empty"
        >
          No items match the selected filters.
        </div>
      ) : (
        <div className={styles.tableFrame}>
          <table className={styles.table} data-test-id="item-list-table">
            <thead>
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      scope="col"
                      aria-sort={sortAriaValue(header.column.getIsSorted())}
                    >
                      {header.isPlaceholder ? null : (
                        <button
                          className={styles.headerButton}
                          type="button"
                          data-test-id={`item-list-sort-${header.id}`}
                          onClick={header.column.getToggleSortingHandler()}
                          aria-label={`Sort by ${String(
                            header.column.columnDef.header,
                          )} (${sortStateLabel(header.column.getIsSorted())})`}
                        >
                          <span>
                            {flexRender(
                              header.column.columnDef.header,
                              header.getContext(),
                            )}
                          </span>
                          <span
                            aria-hidden="true"
                            className={styles.sortIndicator}
                          >
                            {header.column.getIsSorted() === "asc"
                              ? "asc"
                              : header.column.getIsSorted() === "desc"
                                ? "desc"
                                : ""}
                          </span>
                        </button>
                      )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  data-item-id={row.original.id}
                  data-test-id="item-list-row"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
