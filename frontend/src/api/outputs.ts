import { api } from "./client";

/* ── Response types ── */

interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: { message: string; code: number } | null;
}

export interface ResumeListItem {
  id: number;
  name: string;
  created_at: string | null;
}

export interface ResumeProject {
  project_summary_id: number | null;
  project_name: string;
  project_type: string | null;
  project_mode: string | null;
  languages: string[];
  frameworks: string[];
  summary_text: string | null;
  skills: string[];
  text_type: string | null;
  contribution_percent: number | null;
  activities: { name: string; top_file?: string }[];
  key_role: string | null;
  contribution_bullets: string[];
  start_date: string | null;
  end_date: string | null;
}

export interface ResumeDetail {
  id: number;
  name: string;
  created_at: string | null;
  projects: ResumeProject[];
  aggregated_skills: {
    languages: string[];
    frameworks: string[];
    technical_skills: string[];
    writing_skills: string[];
  };
  rendered_text: string | null;
}

export interface RankedProject {
  rank: number;
  project_summary_id: number;
  project_name: string;
  score: number;
  manual_rank: number | null;
}

/* ── Resume API ── */

export function listResumes() {
  return api.get<ApiResponse<{ resumes: ResumeListItem[] }>>("/resume");
}

export function getResume(id: number) {
  return api.get<ApiResponse<ResumeDetail>>(`/resume/${id}`);
}

export function createResume(name: string, projectIds: number[]) {
  return api.postJson<ApiResponse<ResumeDetail>>("/resume/generate", {
    name,
    project_ids: projectIds,
  });
}

export function deleteResume(id: number) {
  return api.delete<ApiResponse<null>>(`/resume/${id}`);
}

/* ── Projects (for resume creation picker) ── */

export function getRankedProjects() {
  return api.get<ApiResponse<{ rankings: RankedProject[] }>>(
    "/projects/ranking"
  );
}

/* ── Resume editing ── */

export interface SkillPreference {
  skill_name: string;
  is_highlighted: boolean;
  display_order?: number;
}

export interface ResumeEditRequest {
  name?: string;
  project_summary_id?: number;
  scope?: "resume_only" | "global";
  display_name?: string;
  summary_text?: string;
  contribution_bullets?: string[];
  contribution_edit_mode?: "append" | "replace";
  key_role?: string;
  skill_preferences?: SkillPreference[];
  skill_preferences_reset?: boolean;
}

export function editResume(resumeId: number, payload: ResumeEditRequest) {
  return api.postJson<ApiResponse<ResumeDetail>>(
    `/resume/${resumeId}/edit`,
    payload
  );
}

/* ── Skill preferences ── */

export interface SkillWithStatus {
  skill_name: string;
  display_name: string;
  is_highlighted: boolean;
  display_order: number | null;
}

export function getResumeSkills(resumeId: number) {
  return api.get<ApiResponse<{ skills: SkillWithStatus[] }>>(
    `/resume/${resumeId}/skills`
  );
}

export function removeProjectFromResume(
  resumeId: number,
  projectName: string
): Promise<ApiResponse<ResumeDetail | null>> {
  const qs = new URLSearchParams({ project_name: projectName });
  return api.delete<ApiResponse<ResumeDetail | null>>(
    `/resume/${resumeId}/projects?${qs}`
  );
}

export function addProjectToResume(
  resumeId: number,
  projectSummaryId: number
): Promise<ApiResponse<ResumeDetail>> {
  return api.postJson<ApiResponse<ResumeDetail>>(
    `/resume/${resumeId}/projects`,
    { project_summary_id: projectSummaryId }
  );
}

/* ── Export helpers ── */

export async function downloadResumeDocx(id: number) {
  const blob = await api.getBlob(`/resume/${id}/export/docx`);
  triggerDownload(blob, `resume_${id}.docx`);
}

export async function downloadResumePdf(id: number) {
  const blob = await api.getBlob(`/resume/${id}/export/pdf`);
  triggerDownload(blob, `resume_${id}.pdf`);
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
