import { api } from "./client";

export type TokenOut = { access_token: string; token_type: string };
export type RegisterOut = { user_id: number; username: string };
type ApiResponse<T> = {
  success: boolean;
  data: T | null;
  error: { message: string; code: number } | null;
};

export function login(username: string, password: string) {
  return api.postJson<TokenOut>("/auth/login", { username, password });
}

export function register(username: string, password: string) {
  return api.postJson<RegisterOut>("/auth/register", { username, password });
}

export function deleteAccount() {
  return api.delete<{ success: boolean }>("/auth/delete-account");
}

export function changePassword(currentPassword: string, newPassword: string) {
  return api.postJson<ApiResponse<null>>("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}
