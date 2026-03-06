import { api } from "./client";
import { tokenStore } from "../auth/token";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export type Project = {
  project_summary_id: number;
  project_key: number | null;
  project_name: string;
  project_type: string | null;
  project_mode: string | null;
  created_at: string | null;
};

export function listProjects(): Promise<Project[]> {
  return api
    .get<{ success: boolean; data: { projects: Project[] } }>("/projects")
    .then((r) => r.data.projects);
}

/** Fetches the thumbnail as a blob URL, or returns null if none exists. */
export async function fetchThumbnailUrl(projectId: number): Promise<string | null> {
  try {
    const token = tokenStore.get();
    const res = await fetch(`${BASE_URL}/projects/${projectId}/thumbnail`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) return null;
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  } catch {
    return null;
  }
}
