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

  // ---------- AI Tutor (Phase 3) ----------
  tutorCreateSession: (body: { mode?: string; locale?: string; subject_id?: string; topic_id?: string; title?: string }) =>
    aiPost<any>("/api/v1/ai/tutor/sessions", body),
  tutorListSessions: () => aiGet<Array<any>>("/api/v1/ai/tutor/sessions"),
  tutorGetSession: (sessionId: string) => aiGet<any>(`/api/v1/ai/tutor/sessions/${sessionId}`),
  tutorDeleteSession: (sessionId: string) => aiDel(`/api/v1/ai/tutor/sessions/${sessionId}`),
  tutorChat: (body: { session_id?: string; message: string; mode?: string; locale?: string; subject_id?: string; topic_id?: string; use_rag?: boolean; use_mcp?: boolean; use_cache?: boolean; top_k?: number }) =>
    aiPost<any>("/api/v1/ai/tutor/chat", body),

  // ---------- Knowledge Map (Phase 3) ----------
  kmListSubjects: (orgId: string) => aiGet<Array<any>>(`/api/v1/ai/knowledge-map/subjects?organization_id=${orgId}`),
  kmCreateSubject: (body: { organization_id: string; name: string; code?: string }) =>
    aiPost<any>("/api/v1/ai/knowledge-map/subjects", body),
  kmListTopics: (subjectId: string) => aiGet<Array<any>>(`/api/v1/ai/knowledge-map/topics?subject_id=${subjectId}`),
  kmCreateTopic: (body: { subject_id: string; name: string; code?: string; order_index?: number }) =>
    aiPost<any>("/api/v1/ai/knowledge-map/topics", body),
  kmListSubtopics: (topicId: string) => aiGet<Array<any>>(`/api/v1/ai/knowledge-map/subtopics?topic_id=${topicId}`),
  kmCreateSubtopic: (body: { topic_id: string; name: string; code?: string; order_index?: number }) =>
    aiPost<any>("/api/v1/ai/knowledge-map/subtopics", body),
  kmListSkills: (subtopicId: string) => aiGet<Array<any>>(`/api/v1/ai/knowledge-map/skills?subtopic_id=${subtopicId}`),
  kmCreateSkill: (body: { subtopic_id: string; name: string; code?: string; order_index?: number }) =>
    aiPost<any>("/api/v1/ai/knowledge-map/skills", body),
  kmGetMap: (studentId: string) => aiGet<any>(`/api/v1/ai/knowledge-map/${studentId}`),
  kmGetMasteryAlgorithm: () => aiGet<any>("/api/v1/ai/knowledge-map/mastery-algorithm"),

  // ---------- Error Analysis (Phase 3) ----------
  eaAnalyze: (body: { student_id?: string; attempt_id?: string; question: string; student_answer?: string; correct_answer?: string; topic_id?: string }) =>
    aiPost<any>("/api/v1/ai/error-analysis", body),
  eaHistory: () => aiGet<Array<any>>("/api/v1/ai/error-analysis/history"),
  eaGet: (analysisId: string) => aiGet<any>(`/api/v1/ai/error-analysis/${analysisId}`),
  eaCategories: () => aiGet<Array<any>>("/api/v1/ai/error-analysis/categories"),

  // ---------- Adaptive Learning / Recommendations (Phase 3) ----------
  recList: (forceRefresh?: boolean) => {
    const qs = forceRefresh ? "?force_refresh=true" : "";
    return aiGet<any>(`/api/v1/ai/recommendations${qs}`);
  },
  recAccept: (recommendationId: string) =>
    aiPost<any>(`/api/v1/ai/recommendations/${recommendationId}/accept`, {}),
  recDismiss: (recommendationId: string) =>
    aiPost<any>(`/api/v1/ai/recommendations/${recommendationId}/dismiss`, {}),
  recAlgorithm: () => aiGet<any>("/api/v1/ai/recommendations/algorithm"),

  // ---------- Learning Paths (Phase 3) ----------
  lpList: () => aiGet<Array<any>>("/api/v1/ai/learning-paths"),
  lpCreate: (body: { title: string; subject_id?: string; target_topic_id?: string; difficulty?: string; steps?: Array<any> }) =>
    aiPost<any>("/api/v1/ai/learning-paths", body),
  lpGet: (pathId: string) => aiGet<any>(`/api/v1/ai/learning-paths/${pathId}`),
  lpUpdate: (pathId: string, body: { title?: string; difficulty?: string; status?: string }) =>
    aiPatch<any>(`/api/v1/ai/learning-paths/${pathId}`, body),
  lpDelete: (pathId: string) => aiDel(`/api/v1/ai/learning-paths/${pathId}`),
  lpCompleteStep: (pathId: string, stepId: string, body: { score?: number }) =>
    aiPost<any>(`/api/v1/ai/learning-paths/${pathId}/steps/${stepId}/complete`, body),
  lpListObjectives: (pathId: string) => aiGet<any>(`/api/v1/ai/learning-paths/${pathId}/objectives`),
  lpAchieveObjective: (pathId: string, objectiveId: string) =>
    aiPost<any>(`/api/v1/ai/learning-paths/${pathId}/objectives/${objectiveId}/achieve`, {}),

  // ---------- Analytics (Phase 3) ----------
  analyticsStudent: (studentId: string) => aiGet<any>(`/api/v1/ai/analytics/student/${studentId}`),
  analyticsTeacher: (teacherId: string) => aiGet<any>(`/api/v1/ai/analytics/teacher/${teacherId}`),
  analyticsParent: (parentId: string) => aiGet<any>(`/api/v1/ai/analytics/parent/${parentId}`),
  analyticsSchool: (orgId: string) => aiGet<any>(`/api/v1/ai/analytics/school/${orgId}`),
};
