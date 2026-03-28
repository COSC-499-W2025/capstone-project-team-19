import { api } from "./client";

export type Project = {
  project_summary_id: number;
  project_key: number | null;
  project_name: string;
  project_type: string | null;
  project_mode: string | null;
  created_at: string | null;
  is_public: boolean;
};

export type ProjectDetail = {
  project_summary_id: number;
  project_key: number | null;
  project_name: string;
  project_type: string | null;
  project_mode: string | null;
  created_at: string | null;
  summary_text: string | null;
  languages: string[];
  frameworks: string[];
  skills: string[];
  contributions: { manual_contribution_summary?: string; [key: string]: unknown };
};

export type ProjectDatesItem = {
  project_summary_id: number;
  project_name: string;
  start_date: string | null;
  end_date: string | null;
  source: "AUTO" | "MANUAL";
  manual_start_date: string | null;
  manual_end_date: string | null;
};

export type FeedbackItem = {
  feedback_id: number | null;
  skill_name: string;
  file_name: string;
  criterion_key: string;
  criterion_label: string;
  expected: string | null;
  suggestion: string | null;
  generated_at: string | null;
};

export function listProjects(): Promise<Project[]> {
  return api
    .get<{ success: boolean; data: { projects: Project[] } }>("/projects")
    .then((r) => r.data.projects);
}

export function getProject(projectId: number): Promise<ProjectDetail> {
  return api
    .get<{ success: boolean; data: ProjectDetail }>(`/projects/${projectId}`)
    .then((r) => r.data);
}

export function deleteProject(projectId: number): Promise<void> {
  return api
    .delete<{ success: boolean }>(`/projects/${projectId}`)
    .then(() => undefined);
}

export async function uploadThumbnail(projectId: number, file: File): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  await api.postMultipart(`/projects/${projectId}/thumbnail`, formData);
}

export function deleteThumbnail(projectId: number): Promise<void> {
  return api
    .delete<{ success: boolean }>(`/projects/${projectId}/thumbnail`)
    .then(() => undefined);
}

export function getProjectDates(projectId: number): Promise<ProjectDatesItem | null> {
  return api
    .get<{ success: boolean; data: { projects: ProjectDatesItem[] } }>("/projects/dates")
    .then((r) => r.data.projects.find((p) => p.project_summary_id === projectId) ?? null);
}

export function patchProjectDates(
  projectId: number,
  start_date: string | null,
  end_date: string | null,
): Promise<ProjectDatesItem> {
  return api
    .patchJson<{ success: boolean; data: ProjectDatesItem }>(
      `/projects/${projectId}/dates`,
      { start_date, end_date },
    )
    .then((r) => r.data);
}

export function resetProjectDates(projectId: number): Promise<ProjectDatesItem> {
  return api
    .delete<{ success: boolean; data: ProjectDatesItem }>(`/projects/${projectId}/dates`)
    .then((r) => r.data);
}

export function patchProjectSummary(
  projectId: number,
  body: { summary_text?: string | null; contribution_summary?: string | null },
): Promise<ProjectDetail> {
  return api
    .patchJson<{ success: boolean; data: ProjectDetail }>(`/projects/${projectId}/summary`, body)
    .then((r) => r.data);
}

export function getProjectFeedback(projectId: number): Promise<FeedbackItem[]> {
  return api
    .get<{ success: boolean; data: { project_id: number; project_name: string; feedback: FeedbackItem[] } }>(
      `/projects/${projectId}/feedback`,
    )
    .then((r) => r.data.feedback)
    .catch(() => []);
}

export type ActivityHeatmapData = {
  project_id: number;
  project_name: string;
  mode: "diff" | "snapshot";
  normalize: boolean;
  include_unclassified_text: boolean;
  matrix: number[][];
  row_labels: string[];
  col_labels: string[];
  title: string;
};

export function getActivityHeatmapData(projectId: number): Promise<ActivityHeatmapData> {
  return api
    .get<{ success: boolean; data: ActivityHeatmapData }>(
      `/projects/${projectId}/activity-heatmap/data`
    )
    .then((r) => r.data);
}

/** Fetches the thumbnail as a blob URL, or returns null if none exists. */
export async function fetchThumbnailUrl(projectId: number): Promise<string | null> {
  try {
    const blob = await api.getBlob(`/projects/${projectId}/thumbnail`);
    return URL.createObjectURL(blob);
  } catch {
    return null;
  }
}
