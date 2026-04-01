import { apiFetch } from "./api";

interface LoginResponse {
  access_token: string;
  token_type: string;
  role: string;
  name: string;
}

interface AuthUser {
  token: string;
  role: string;
  name: string;
}

export async function login(
  email: string,
  password: string
): Promise<AuthUser> {
  const data = await apiFetch<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  localStorage.setItem("token", data.access_token);
  localStorage.setItem("role", data.role);
  localStorage.setItem("name", data.name);

  return { token: data.access_token, role: data.role, name: data.name };
}

export function getAuth(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");
  const name = localStorage.getItem("name");
  if (!token || !role || !name) return null;
  return { token, role, name };
}

export function logout(): void {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("name");
}

export function isAuthenticated(): boolean {
  return getAuth() !== null;
}
