import { api } from "./client";

export type TokenOut = { access_token: string; token_type: string };
export type RegisterOut = { user_id: number; username: string };

export function login(username: string, password: string) {
  return api.postJson<TokenOut>("/auth/login", { username, password });
}

export function register(username: string, password: string) {
  return api.postJson<RegisterOut>("/auth/register", { username, password });
}

export function logout() {
  return api.post<{ success: boolean }>("/auth/logout");
}

export function deleteAccount() {
  return api.delete<{ success: boolean }>("/auth/delete-account");
}