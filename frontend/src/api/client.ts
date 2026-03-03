import { tokenStore } from "../auth/token";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = tokenStore.get();

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!res.ok) {
    const raw = await res.text();
    let msg = raw;

    try {
      const parsed = JSON.parse(raw);
      if (typeof parsed?.detail === "string") msg = parsed.detail;
      else if (Array.isArray(parsed?.detail)) {
        msg = parsed.detail.map((d: any) => d?.msg).filter(Boolean).join(", ");
      }
    } catch {
      // keep raw text
    }

    throw new Error(msg || `${res.status} ${res.statusText}`);
  }

  // some endpoints might return empty body
  const text = await res.text();
  return (text ? (JSON.parse(text) as T) : ({} as T));
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  postJson: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};