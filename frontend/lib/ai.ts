// AI Core API client service (reuses Phase 1 auth cookie pattern).
const API_BASE =
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL
    : "http://localhost:8000";

async function aiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> || {}),
  };
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  return res;
}

export async function aiGet<T = unknown>(path: string): Promise<T> {
  const res = await aiFetch(path);
  if (!res.ok) throw new Error(`AI API ${path} ${res.status}`);
  return (await res.json()) as T;
}

export async function aiPost<T = unknown>(path: string, body: unknown): Promise<T> {
  const res = await aiFetch(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`AI API ${path} ${res.status}`);
  return (await res.json()) as T;
}

export async function aiPatch<T = unknown>(path: string, body: unknown): Promise<T> {
  const res = await aiFetch(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`AI API ${path} ${res.status}`);
  return (await res.json()) as T;
}

export async function aiDel(path: string): Promise<void> {
  const res = await aiFetch(path, { method: "DELETE" });
  if (!res.ok) throw new Error(`AI API ${path} ${res.status}`);
}

export const aiService = {
  health: () => aiGet<{ status: string; components: Record<string, string> }>("/api/v1/ai/health"),
  config: () => aiGet<Record<string, unknown>>("/api/v1/ai/config/status"),
  listPrompts: () => aiGet<Array<any>>("/api/v1/ai/prompts"),
  createPrompt: (body: any) => aiPost<any>("/api/v1/ai/prompts", body),
  updatePrompt: (id: string, body: any) => aiPatch<any>(`/api/v1/ai/prompts/${id}`, body),
  deletePrompt: (id: string) => aiDel(`/api/v1/ai/prompts/${id}`),
  listDocuments: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return aiGet<Array<any>>(`/api/v1/ai/documents${qs}`);
  },
  createDocument: (body: any) => aiPost<any>("/api/v1/ai/documents", body),
  ragSearch: (body: any) => aiPost<any>("/api/v1/ai/rag/search", body),
  listTools: () => aiGet<Array<any>>("/api/v1/ai/tools"),
  executeTool: (name: string, body: any) => aiPost<any>(`/api/v1/ai/tools/${name}/execute`, body),
  listTraces: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return aiGet<Array<any>>(`/api/v1/ai/traces${qs}`);
  },
  listSecurityEvents: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return aiGet<Array<any>>(`/api/v1/ai/security/events${qs}`);
  },
};
