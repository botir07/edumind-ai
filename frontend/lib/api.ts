import Cookies from "js-cookie";

const API_BASE =
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL
    : "http://localhost:8000";

export type ApiError = {
  code?: string;
  message?: string;
  details?: unknown;
};

class ApiErrorClass extends Error {
  code?: string;
  status: number;
  details?: unknown;
  constructor(status: number, message: string, code?: string, details?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
    this.name = "ApiError";
  }
}

async function request(
  input: RequestInfo | URL,
  init: RequestInit = {}
): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> || {}),
  };

  const url = typeof input === "string" ? input : String(input);
  const fullUrl = url.startsWith("http") ? url : `${API_BASE}${url}`;
  const res = await fetch(fullUrl, {
    ...init,
    headers,
    credentials: "include",
  });

  if (res.status === 401) {
    // Try refresh once
    try {
      const refreshRes = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
      if (refreshRes.ok) {
        // retry original request
        return fetch(fullUrl, {
          ...init,
          headers,
          credentials: "include",
        });
      }
    } catch {
      // refresh failed; fall through to 401
    }
  }
  return res;
}

export async function apiFetch<T = unknown>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const res = await request(path, init);
  if (!res.ok) {
    let message = res.statusText;
    let code: string | undefined;
    let details: unknown;
    try {
      const body = (await res.json()) as { error?: { message?: string; code?: string; details?: unknown } };
      message = body.error?.message || message;
      code = body.error?.code;
      details = body.error?.details;
    } catch {
      // ignore
    }
    throw new ApiErrorClass(res.status, message, code, details);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json") && res.status !== 204) {
    return (await res.json()) as T;
  }
  return (await res.text()) as unknown as T;
}

export const authService = {
  async login(email: string, password: string) {
    const body: { email: string; password: string } = { email, password };
    const res = await request("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
      credentials: "include",
    });
    if (!res.ok) throw new ApiErrorClass(res.status, "Invalid email or password");
    const data = (await res.json()) as { access_token: string; refresh_token: string };
    return data;
  },
  async logout() {
    await request("/api/v1/auth/logout", { method: "POST", credentials: "include" });
    Cookies.remove("access_token");
    Cookies.remove("refresh_token");
  },
  async refresh() {
    const res = await request("/api/v1/auth/refresh", { method: "POST", credentials: "include" });
    if (!res.ok) throw new ApiErrorClass(res.status, "Refresh failed");
    return res.json();
  },
  async me() {
    return apiFetch<{ user: any; memberships: any[] }>("/api/v1/auth/me");
  },
  async forgotPassword(email: string) {
    return apiFetch("/api/v1/auth/password/forgot", { method: "POST", body: JSON.stringify({ email }) });
  },
  async resetPassword(token: string, newPassword: string) {
    return apiFetch("/api/v1/auth/password/reset", { method: "POST", body: JSON.stringify({ token, new_password: newPassword }) });
  },
  async changePassword(current: string, newPass: string) {
    return apiFetch("/api/v1/auth/password/change", { method: "POST", body: JSON.stringify({ current_password: current, new_password: newPass }) });
  },
};

export { API_BASE, ApiErrorClass };
