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

export interface PortfolioProject {
  project_summary_id: number | null;
  project_name: string;
  display_name: string;
  project_type: string | null;
  project_mode: string | null;
  score: number;
  duration: string | null;
  languages: string[];
  frameworks: string[];
  activity: string | null;
  skills: string[];
  summary_text: string | null;
  contribution_bullets: string[];
}

export interface PortfolioDetail {
  projects: PortfolioProject[];
  rendered_text: string | null;
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
  return api.del<ApiResponse<null>>(`/resume/${id}`);
}

/* ── Portfolio API ── */

export function getPortfolio() {
  return api.get<ApiResponse<PortfolioDetail>>("/portfolio/generate", );
}

/* ── Projects (for resume creation picker) ── */

export function getRankedProjects() {
  return api.get<ApiResponse<{ rankings: RankedProject[] }>>(
    "/projects/ranking"
  );
}

/* ── Export helpers ── */

export async function downloadResumeDocx(id: number) {
  const blob = await api.downloadBlob(`/resume/${id}/export/docx`);
  triggerDownload(blob, `resume_${id}.docx`);
}

export async function downloadResumePdf(id: number) {
  const blob = await api.downloadBlob(`/resume/${id}/export/pdf`);
  triggerDownload(blob, `resume_${id}.pdf`);
}

export async function downloadPortfolioDocx() {
  const blob = await api.downloadBlob("/portfolio/export/docx");
  triggerDownload(blob, "portfolio.docx");
}

export async function downloadPortfolioPdf() {
  const blob = await api.downloadBlob("/portfolio/export/pdf");
  triggerDownload(blob, "portfolio.pdf");
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
