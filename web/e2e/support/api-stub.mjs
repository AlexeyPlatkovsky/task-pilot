import { createServer } from "node:http";

const port = Number(process.env.TASKPILOT_E2E_API_PORT ?? "7152");
const archivedItem = { id: "TP-1", title: "Archived E2E item", type: "task", status: "done", priority: "normal", valid: true, findings: [], created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" };
const archivedFeature = { id: "TP-2", title: "Archived feature", type: "feature", status: "cancelled", priority: "high", valid: true, findings: [], created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" };
let items = [];
let archived = [archivedItem, archivedFeature];

createServer((request, response) => {
  response.setHeader("Content-Type", "application/json");

  if (request.url === "/api/health") {
    response.end(JSON.stringify({ status: "ok" }));
    return;
  }

  if (request.url === "/api/projects") {
    response.end(JSON.stringify([{ id: "taskpilot-e2e", key: "TP", name: "TaskPilot E2E", active: true }]));
    return;
  }

  if (request.url === "/api/ui-state") {
    response.end(JSON.stringify({ last_opened_project_id: "taskpilot-e2e" }));
    return;
  }

  if (request.url === "/api/projects/taskpilot-e2e/validate") {
    response.end(JSON.stringify({ ok: true, summary: { errors: 0, warnings: 0 }, findings: [] }));
    return;
  }

  if (request.url === "/api/projects/taskpilot-e2e/items") {
    response.end(JSON.stringify(items));
    return;
  }

  if (request.url === "/api/projects/taskpilot-e2e/archived") {
    response.end(JSON.stringify(archived));
    return;
  }

  if (request.method === "POST" && request.url === "/api/projects/taskpilot-e2e/items/TP-1/unarchive") {
    items = [archivedItem];
    archived = [archivedFeature];
    response.end(JSON.stringify(archivedItem));
    return;
  }

  response.statusCode = 404;
  response.end(JSON.stringify({ detail: "Not found" }));
}).listen(port, "127.0.0.1");
