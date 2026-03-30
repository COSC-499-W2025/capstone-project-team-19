import { tokenStore } from "../auth/token";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

function handleUnauthorized() {
  tokenStore.clear();

  // Avoid redirect loop if already on auth pages
  if (
    window.location.pathname !== "/login" &&
    window.location.pathname !== "/register"
  ) {
    window.location.replace("/login");
  }
}

function parseErrorMessage(raw: string, fallback: string): string {
  let msg = raw || fallback;

  try {
    const parsed = JSON.parse(raw);

    if (typeof parsed?.detail === "string") {
      msg = parsed.detail;
    } else if (Array.isArray(parsed?.detail)) {
      msg = parsed.detail
        .map((e: unknown) => {
          const err = e as { loc?: unknown; msg?: string };
          const loc = Array.isArray(err?.loc) ? err.loc : [];
          const field = loc.length ? String(loc[loc.length - 1]) : "";
          const label = field ? field.charAt(0).toUpperCase() + field.slice(1) : "Input";
          return `${label}: ${err?.msg ?? "Invalid value"}`;
        })
        .join("\n");
    }
  } catch {
    // keep raw
  }

  return msg;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = tokenStore.get();

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (res.status === 401) {
    handleUnauthorized();
    throw new Error("Could not validate credentials");
  }

  if (!res.ok) {
    const raw = await res.text();
    throw new Error(parseErrorMessage(raw, `${res.status} ${res.statusText}`));
  }

  const text = await res.text();
  return text ? (JSON.parse(text) as T) : ({} as T);
}

export const api = {
  get: <T>(path: string) => request<T>(path),

  postJson: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  postForm: <T>(path: string, form: FormData) =>
    request<T>(path, {
      method: "POST",
      body: form,
    }),

  putJson: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: "PUT",
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

  getBlob: async (path: string): Promise<Blob> => {
    const token = tokenStore.get();

    const res = await fetch(`${BASE_URL}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (res.status === 401) {
      handleUnauthorized();
      throw new Error("Could not validate credentials");
    }

    if (!res.ok) {
      const raw = await res.text();
      throw new Error(parseErrorMessage(raw, `${res.status} ${res.statusText}`));
    }

    return await res.blob();
  },

  post: <T>(path: string) => request<T>(path, { method: "POST" }),
};