import { useMemo, useState } from "react";
import type { ItemSummary } from "../types";
import {
  STATUS_LABELS,
  TYPE_LABELS,
} from "../types/labels";
import styles from "./ItemTreeView.module.css";

interface Props {
  items: ItemSummary[];
  onItemClick: (itemId: string) => void;
}

interface TreeNodeData {
  item: ItemSummary;
  children: TreeNodeData[];
}

function numericIdKey(item: ItemSummary): [number, string] {
  const suffix = item.id.split("-").pop();
  const value = suffix ? Number.parseInt(suffix, 10) : Number.NaN;
  return [Number.isNaN(value) ? -1 : value, item.id];
}

function sortItems(items: ItemSummary[]): ItemSummary[] {
  return [...items].sort((a, b) => {
    const [aNum, aId] = numericIdKey(a);
    const [bNum, bId] = numericIdKey(b);
    return aNum - bNum || aId.localeCompare(bId);
  });
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

function buildTree(items: ItemSummary[]): TreeNodeData[] {
  const itemById = new Map(items.map((item) => [item.id, item]));
  const childrenByParent = new Map<string, ItemSummary[]>();

  for (const item of items) {
    if (!item.parent_id || !itemById.has(item.parent_id)) {
      continue;
    }
    const siblings = childrenByParent.get(item.parent_id) ?? [];
    siblings.push(item);
    childrenByParent.set(item.parent_id, siblings);
  }

  const roots = sortItems(
    items.filter((item) => !item.parent_id || !itemById.has(item.parent_id)),
  );
  const safeRoots = roots.length > 0 ? roots : sortItems(items);

  function nodeFor(item: ItemSummary, ancestors: Set<string>): TreeNodeData {
    const nextAncestors = new Set(ancestors);
    nextAncestors.add(item.id);
    const children = sortItems(childrenByParent.get(item.id) ?? [])
      .filter((child) => !nextAncestors.has(child.id))
      .map((child) => nodeFor(child, nextAncestors));
    return { item, children };
  }

  return safeRoots.map((item) => nodeFor(item, new Set()));
}

function TreeNode({
  node,
  depth,
  expanded,
  onToggle,
  onItemClick,
}: {
  node: TreeNodeData;
  depth: number;
  expanded: Set<string>;
  onToggle: (itemId: string) => void;
  onItemClick: (itemId: string) => void;
}) {
  const hasChildren = node.children.length > 0;
  const isExpanded = expanded.has(node.item.id);

  return (
    <li>
      <div
        className={styles.treeItem}
        role="treeitem"
        aria-level={depth}
        aria-expanded={hasChildren ? isExpanded : undefined}
      >
        <div className={styles.nodeMain}>
          {hasChildren ? (
            <button
              className={styles.expandButton}
              type="button"
              onClick={() => onToggle(node.item.id)}
              aria-label={`${isExpanded ? "Collapse" : "Expand"} ${
                node.item.id
              }`}
            >
              {isExpanded ? "v" : ">"}
            </button>
          ) : (
            <span className={styles.leafSpacer} aria-hidden="true" />
          )}
          <span className={styles.itemId}>{node.item.id}</span>
          <button
            className={styles.titleButton}
            type="button"
            onClick={() => onItemClick(node.item.id)}
            disabled={!node.item.valid}
            aria-label={`Open ${node.item.id}`}
          >
            {node.item.title}
          </button>
        </div>
        <div className={styles.meta}>
          <span>{labelFor(TYPE_LABELS, node.item.type)}</span>
          <span>{labelFor(STATUS_LABELS, node.item.status)}</span>
        </div>
      </div>
      {hasChildren && isExpanded ? (
        <ul className={styles.children} role="group">
          {node.children.map((child) => (
            <TreeNode
              key={child.item.id}
              node={child}
              depth={depth + 1}
              expanded={expanded}
              onToggle={onToggle}
              onItemClick={onItemClick}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function ItemTreeView({ items, onItemClick }: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const tree = useMemo(() => buildTree(items), [items]);

  const toggle = (itemId: string) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(itemId)) {
        next.delete(itemId);
      } else {
        next.add(itemId);
      }
      return next;
    });
  };

  if (items.length === 0) {
    return (
      <div className={styles.emptyState}>
        No hierarchy yet.
      </div>
    );
  }

  return (
    <div className={styles.treeFrame}>
      <ul className={styles.tree} role="tree" aria-label="Item hierarchy">
        {tree.map((node) => (
          <TreeNode
            key={node.item.id}
            node={node}
            depth={1}
            expanded={expanded}
            onToggle={toggle}
            onItemClick={onItemClick}
          />
        ))}
      </ul>
    </div>
  );
}
