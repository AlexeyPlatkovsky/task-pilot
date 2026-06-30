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
import { WORKFLOW_STATUSES } from "../types";
import {
  PRIORITY_LABELS,
  STATUS_LABELS,
  TYPE_LABELS,
} from "../types/labels";
import { DropdownSelect, type DropdownOption } from "./DropdownSelect";
import { FilterBar } from "./FilterBar";
import {
  isWithinTimeRange,
  TYPE_FILTER_OPTIONS,
  PRIORITY_FILTER_OPTIONS,
  UPDATED_FILTER_OPTIONS,
  CREATED_FILTER_OPTIONS,
  type TimeRange,
} from "./filters";
import styles from "./ItemListView.module.css";

interface Props {
  items: ItemSummary[];
  onItemClick: (itemId: string) => void;
  now?: Date;
}

interface Filters {
  status: string;
  type: string;
  priority: string;
  timeRange: TimeRange;
  createdRange: TimeRange;
}

const DEFAULT_FILTERS: Filters = {
  status: "",
  type: "",
  priority: "",
  timeRange: "all",
  createdRange: "all",
};

const STATUS_FILTER_OPTIONS: DropdownOption[] = [
  { value: "", label: "All statuses" },
  ...WORKFLOW_STATUSES.map((status) => ({
    value: status,
    label: STATUS_LABELS[status],
  })),
];

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

function sortIndicatorLabel(sortState: false | "asc" | "desc"): string {
  if (sortState === "asc") {
    return "▲▽";
  }
  if (sortState === "desc") {
    return "△▼";
  }
  return "△▽";
}

export function ItemListView({
  items,
  onItemClick,
  now,
}: Props) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [defaultNow] = useState(() => new Date());
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const filterNow = now ?? defaultNow;
  const hasActiveFilters =
    filters.status !== DEFAULT_FILTERS.status ||
    filters.type !== DEFAULT_FILTERS.type ||
    filters.priority !== DEFAULT_FILTERS.priority ||
    filters.timeRange !== DEFAULT_FILTERS.timeRange ||
    filters.createdRange !== DEFAULT_FILTERS.createdRange;

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
        if (!isWithinTimeRange(item, filters.timeRange, "updated_at", filterNow)) {
          return false;
        }
        if (!isWithinTimeRange(item, filters.createdRange, "created_at", filterNow)) {
          return false;
        }
        return true;
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
      <FilterBar
        hasActiveFilters={hasActiveFilters}
        onClear={() => setFilters(DEFAULT_FILTERS)}
        ariaLabel="List filters"
        dataTestId="item-list-filters"
      >
        <DropdownSelect
          id="item-list-filter-status"
          label="Status"
          value={filters.status}
          options={STATUS_FILTER_OPTIONS}
          fieldDataTestId="item-list-filter-field"
          onChange={(status) =>
            setFilters((current) => ({ ...current, status }))
          }
        />

        <DropdownSelect
          id="item-list-filter-type"
          label="Type"
          value={filters.type}
          options={TYPE_FILTER_OPTIONS}
          fieldDataTestId="item-list-filter-field"
          onChange={(type) => setFilters((current) => ({ ...current, type }))}
        />

        <DropdownSelect
          id="item-list-filter-priority"
          label="Priority"
          value={filters.priority}
          options={PRIORITY_FILTER_OPTIONS}
          fieldDataTestId="item-list-filter-field"
          onChange={(priority) =>
            setFilters((current) => ({ ...current, priority }))
          }
        />

        <DropdownSelect
          id="item-list-filter-updated"
          label="Updated"
          value={filters.timeRange}
          options={UPDATED_FILTER_OPTIONS}
          fieldDataTestId="item-list-filter-field"
          onChange={(timeRange) =>
            setFilters((current) => ({ ...current, timeRange }))
          }
        />

        <DropdownSelect
          id="item-list-filter-created"
          label="Created"
          value={filters.createdRange}
          options={CREATED_FILTER_OPTIONS}
          fieldDataTestId="item-list-filter-field"
          onChange={(createdRange) =>
            setFilters((current) => ({ ...current, createdRange }))
          }
        />
      </FilterBar>

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
                            {sortIndicatorLabel(header.column.getIsSorted())}
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
