import { apiRequest, setTokens, clearSession } from "./api.js";
import { STORAGE_KEYS } from "./config.js";

export interface VOAUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar?: string | null;
  style_preference?: string;
}

interface AuthSuccess {
  tokens: { access: string; refresh: string };
  user: VOAUser;
}

interface AuthError {
  errors?: {
    non_field_errors?: string[];
    detail?: string;
    [field: string]: string[] | string | undefined;
  };
}

export async function login(email: string, password: string) {
  const res = await apiRequest<AuthSuccess | AuthError>(
    "/auth/login/",
    { method: "POST", body: { email, password }, auth: false }
  );
  if (res.ok) {
    const data = res.data as AuthSuccess;
    setTokens(data.tokens.access, data.tokens.refresh);
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(data.user));
  }
  return res;
}

export async function register(payload: {
  username: string; email: string; first_name: string; last_name: string;
  password: string; password_confirm: string; style_preference?: string;
}) {
  return apiRequest("/auth/register/", { method: "POST", body: payload, auth: false });
}

export async function forgotPassword(email: string) {
  return apiRequest("/auth/forgot-password/", { method: "POST", body: { email }, auth: false });
}

export async function resetPassword(token: string, new_password: string) {
  return apiRequest("/auth/reset-password/", { method: "POST", body: { token, new_password }, auth: false });
}

export function logout(): void {
  clearSession();
  window.location.href = "/pages/login.html";
}

export function getCurrentUser(): VOAUser | null {
  const raw = localStorage.getItem(STORAGE_KEYS.USER);
  return raw ? JSON.parse(raw) : null;
}

export function requireAuth(): void {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  if (!token) {
    window.location.href = "/pages/login.html";
  }
}
