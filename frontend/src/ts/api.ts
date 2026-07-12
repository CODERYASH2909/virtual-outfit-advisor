import { API_BASE_URL, STORAGE_KEYS } from "./config.js";

export interface ApiResponse<T> {
  ok: boolean;
  status: number;
  data: T;
}

function getAccessToken(): string | null {
  return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
}

function getRefreshToken(): string | null {
  return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
}

function setTokens(access: string, refresh?: string): void {
  localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, access);
  if (refresh) localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refresh);
}

export function clearSession(): void {
  localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.USER);
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;

  const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!response.ok) return false;
  const data = await response.json();
  setTokens(data.access);
  return true;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  isFormData?: boolean;
  auth?: boolean;
}

/**
 * Central fetch wrapper: attaches JWT auth headers, retries once on 401
 * after refreshing the access token, and normalizes the response shape.
 */
export async function apiRequest<T = any>(
  path: string,
  options: RequestOptions = {}
): Promise<ApiResponse<T>> {
  const { method = "GET", body, isFormData = false, auth = true } = options;

  const headers: Record<string, string> = {};
  if (!isFormData) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const doFetch = () =>
    fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? (isFormData ? (body as FormData) : JSON.stringify(body)) : undefined,
    });

  let response: Response;
  try {
    response = await doFetch();
  } catch (error) {
    console.error("Network error:", error);
    return {
      ok: false,
      status: 0,
      data: { errors: { detail: "Cannot connect to the server. Please ensure the backend is running at http://localhost:8000" } } as unknown as T
    };
  }

  if (response.status === 401 && auth) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      const token = getAccessToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
      try {
        response = await doFetch();
      } catch (error) {
        return {
          ok: false,
          status: 0,
          data: { errors: { detail: "Cannot connect to the server. Please ensure the backend is running at http://localhost:8000" } } as unknown as T
        };
      }
    } else {
      clearSession();
      window.location.href = "/pages/login.html";
      return { ok: false, status: 401, data: {} as T };
    }
  }

  let data: T;
  try {
    data = response.status === 204 ? ({} as T) : await response.json();
  } catch {
    data = {} as T;
  }

  return { ok: response.ok, status: response.status, data };
}

export { setTokens, getAccessToken };
