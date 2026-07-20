const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "/backend";

export type AuthSession = {
  token: string;
  role: "hr" | "department";
  displayName: string;
};

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = window.localStorage.getItem("recruitflow_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function requireOk(response: Response): Promise<void> {
  if (response.status === 401 && typeof window !== "undefined") {
    clearSession();
    window.dispatchEvent(new Event("recruitflow:unauthorized"));
  }
  if (!response.ok) throw new Error(await response.text());
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store", headers: authHeaders() });
  await requireOk(response);
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    headers: {
      ...authHeaders(),
      ...(body && !(body instanceof FormData) ? { "Content-Type": "application/json" } : {})
    }
  });
  await requireOk(response);
  return response.json() as Promise<T>;
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  await requireOk(response);
  return response.json() as Promise<T>;
}

export function saveSession(accessToken: string, role: string, displayName: string): void {
  window.localStorage.setItem("recruitflow_token", accessToken);
  window.localStorage.setItem("recruitflow_role", role);
  window.localStorage.setItem("recruitflow_display_name", displayName);
}

export function clearSession(): void {
  window.localStorage.removeItem("recruitflow_token");
  window.localStorage.removeItem("recruitflow_role");
  window.localStorage.removeItem("recruitflow_display_name");
}

export function getSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  const token = window.localStorage.getItem("recruitflow_token");
  const role = window.localStorage.getItem("recruitflow_role");
  const displayName = window.localStorage.getItem("recruitflow_display_name");
  if (!token || !displayName || (role !== "hr" && role !== "department")) return null;
  return { token, role, displayName };
}

export function maskPhone(value: string | null): string {
  if (!value) return "-";
  const digits = value.replace(/\D/g, "");
  if (digits.length < 7) return "***";
  return `${digits.slice(0, 3)}****${digits.slice(-4)}`;
}

export function maskEmail(value: string | null): string {
  if (!value) return "-";
  const [local, domain] = value.split("@");
  if (!domain) return "***";
  return `${local.slice(0, 2)}***@${domain}`;
}
