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
    let msg = raw || `${res.status} ${res.statusText}`;

    try {
      const parsed = JSON.parse(raw);

      // FastAPI error shape: { detail: "..." } or { detail: [ { loc, msg, type }, ... ] }
      if (typeof parsed?.detail === "string") {
        msg = parsed.detail;
      } else if (Array.isArray(parsed?.detail)) {
        msg = parsed.detail
          .map((e: any) => {
            const loc = Array.isArray(e?.loc) ? e.loc : [];
            const field = loc.length ? String(loc[loc.length - 1]) : "";
            const label = field ? field.charAt(0).toUpperCase() + field.slice(1) : "Input";
            return `${label}: ${e?.msg ?? "Invalid value"}`;
          })
          .join("\n");
      }
    } catch {
      // keep raw
    }

    throw new Error(msg);
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
  patchJson: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  postMultipart: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: "POST", body: formData }),
};