import { api } from "./client";
import type { SkillTimelineDTO, ActivityByDateMatrixDTO } from "./insights";
import type { ActivityHeatmapData } from "./projects";

interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: { message: string; code: number } | null;
}

/* ── Public DTOs (stripped of internal fields) ── */

export interface PublicProject {
  project_summary_id: number;
  project_name: string;
  project_type: string | null;
  project_mode: string | null;
  created_at: string | null;
}

export interface PublicProjectDetail {
  project_summary_id: number;
  project_name: string;
  project_type: string | null;
  project_mode: string | null;
  created_at: string | null;
  start_date: string | null;
  end_date: string | null;
  summary_text: string | null;
  contribution_summary: string | null;
  languages: string[];
  frameworks: string[];
  skills: string[];
}

export interface PublicRankingItem {
  rank: number;
  project_summary_id: number;
  project_name: string;
}

export interface PublicResumeListItem {
  id: number;
  name: string;
  created_at: string | null;
}

export interface PublicResumeProject {
  project_name: string;
  project_type: string | null;
  project_mode: string | null;
  languages: string[];
  frameworks: string[];
  summary_text: string | null;
  skills: string[];
  key_role: string | null;
  contribution_bullets: string[];
  start_date: string | null;
  end_date: string | null;
}

export interface PublicResumeDetail {
  id: number;
  name: string;
  created_at: string | null;
  projects: PublicResumeProject[];
  aggregated_skills: {
    languages: string[];
    frameworks: string[];
    technical_skills: string[];
    writing_skills: string[];
    advanced?: string[];
    intermediate?: string[];
    beginner?: string[];
  };
  rendered_text: string | null;
}

export interface PublicSkill {
  skill_name: string;
  level: string;
  project_name: string;
}

/* ── API functions ── */

export interface PublicPortfolioStatus {
  exists: boolean;
  is_public: boolean;
}

export function publicGetPortfolioStatus(username: string): Promise<PublicPortfolioStatus> {
  return api.get<PublicPortfolioStatus>(`/public/${username}/status`);
}

export function publicListProjects(username: string): Promise<PublicProject[]> {
  return api
    .get<ApiResponse<{ projects: PublicProject[] }>>(`/public/${username}/projects`)
    .then((r) => r.data?.projects ?? []);
}

export function publicGetProject(
  username: string,
  projectId: number,
): Promise<PublicProjectDetail | null> {
  return api
    .get<ApiResponse<PublicProjectDetail>>(`/public/${username}/projects/${projectId}`)
    .then((r) => r.data ?? null);
}

export function publicGetRanking(username: string): Promise<PublicRankingItem[]> {
  return api
    .get<ApiResponse<{ rankings: PublicRankingItem[] }>>(`/public/${username}/ranking`)
    .then((r) => r.data?.rankings ?? []);
}

export function publicListResumes(username: string): Promise<PublicResumeListItem[]> {
  return api
    .get<ApiResponse<{ resumes: PublicResumeListItem[] }>>(`/public/${username}/resumes`)
    .then((r) => r.data?.resumes ?? []);
}

export function publicGetResume(
  username: string,
  resumeId: number,
): Promise<PublicResumeDetail | null> {
  return api
    .get<ApiResponse<PublicResumeDetail>>(`/public/${username}/resumes/${resumeId}`)
    .then((r) => r.data ?? null);
}

export function publicGetActiveResume(username: string): Promise<PublicResumeDetail | null> {
  return api
    .get<ApiResponse<PublicResumeDetail>>(`/public/${username}/active-resume`)
    .then((r) => r.data ?? null);
}

export function publicGetSkills(username: string): Promise<PublicSkill[]> {
  return api
    .get<ApiResponse<{ skills: PublicSkill[] }>>(`/public/${username}/skills`)
    .then((r) => r.data?.skills ?? []);
}

export function publicGetSkillsTimeline(username: string): Promise<SkillTimelineDTO> {
  return api
    .get<{ success: boolean; data: SkillTimelineDTO }>(`/public/${username}/skills/timeline`)
    .then((r) => r.data);
}

export function publicGetActivityByDate(username: string, year?: number | null): Promise<ActivityByDateMatrixDTO> {
  const params = year != null ? `?year=${year}` : "";
  return api
    .get<{ success: boolean; data: ActivityByDateMatrixDTO }>(`/public/${username}/skills/activity-by-date${params}`)
    .then((r) => r.data);
}

export function publicGetActivityHeatmapData(username: string, projectId: number): Promise<ActivityHeatmapData> {
  return api
    .get<{ success: boolean; data: ActivityHeatmapData }>(`/public/${username}/projects/${projectId}/activity-heatmap/data`)
    .then((r) => r.data);
}

export async function publicDownloadResumeDocx(username: string, resumeId: number): Promise<void> {
  const blob = await api.getBlob(`/public/${username}/resumes/${resumeId}/export/docx`);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `resume_${resumeId}.docx`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function publicDownloadResumePdf(username: string, resumeId: number): Promise<void> {
  const blob = await api.getBlob(`/public/${username}/resumes/${resumeId}/export/pdf`);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `resume_${resumeId}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function publicFetchThumbnailUrl(
  username: string,
  projectId: number,
): Promise<string | null> {
  try {
    const blob = await api.getBlob(`/public/${username}/projects/${projectId}/thumbnail`);
    return URL.createObjectURL(blob);
  } catch {
    return null;
  }
}
