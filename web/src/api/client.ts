import type {
  ApiError,
  ItemDetail,
  ItemSummary,
  ItemUpdateInput,
  ProjectSummary,
  ValidationReport,
} from "../types";

const BASE_URL = "/api";

class TaskPilotApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "TaskPilotApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as ApiError;
      message = body.detail ?? message;
    } catch {
      // ignore parse error
    }
    throw new TaskPilotApiError(response.status, message);
  }

  return (await response.json()) as T;
}

export async function fetchProjects(): Promise<ProjectSummary[]> {
  return request<ProjectSummary[]>("/projects");
}

export async function fetchItems(projectId: string): Promise<ItemSummary[]> {
  return request<ItemSummary[]>(`/projects/${projectId}/items`);
}

export async function fetchItem(
  projectId: string,
  itemId: string,
): Promise<ItemDetail> {
  return request<ItemDetail>(`/projects/${projectId}/items/${itemId}`);
}

export async function fetchValidationReport(
  projectId: string,
): Promise<ValidationReport> {
  return request<ValidationReport>(`/projects/${projectId}/validate`);
}

export async function updateItem(
  projectId: string,
  itemId: string,
  input: ItemUpdateInput,
): Promise<ItemDetail> {
  return request<ItemDetail>(`/projects/${projectId}/items/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}
