import { api } from "./client";
import type { Project, ProjectDetail } from "./projects";
import type { ProjectRankingDTO } from "./insights";
import type { SkillTimelineApiResponse } from "./insights";
import type { ResumeListItem, ResumeDetail } from "./outputs";

export function publicListProjects(username: string): Promise<Project[]> {
  return api
    .get<{ success: boolean; data: { projects: Project[] } }>(`/public/${username}/projects`)
    .then((r) => r.data.projects);
}

export function publicGetProject(username: string, projectId: number): Promise<ProjectDetail> {
  return api
    .get<{ success: boolean; data: ProjectDetail }>(`/public/${username}/projects/${projectId}`)
    .then((r) => r.data);
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

/** Returns the same shape as getRanking() so it can be used interchangeably. */
export function publicGetRanking(username: string): Promise<ProjectRankingDTO> {
  return api.get<ProjectRankingDTO>(`/public/${username}/ranking`);
}

/** Returns the same shape as getSkillTimeline() so it can be used interchangeably. */
export function publicGetSkillsTimeline(username: string): Promise<SkillTimelineApiResponse> {
  return api.get<SkillTimelineApiResponse>(`/public/${username}/skills/timeline`);
}

export function publicListResumes(username: string): Promise<{ data: { resumes: ResumeListItem[] } }> {
  return api.get(`/public/${username}/resumes`);
}

export function publicGetResume(username: string, resumeId: number): Promise<{ data: ResumeDetail }> {
  return api.get(`/public/${username}/resumes/${resumeId}`);
}
