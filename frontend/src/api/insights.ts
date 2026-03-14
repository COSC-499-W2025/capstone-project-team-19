import { api } from "./client";

const BASE_URL = "/projects";

// Get Project Ranking (returns a list of all projects in their ranked order)

export type RankedProject = {
    rank: number;
    project_summary_id: number;
    project_name: string;
    score: number;
    manual_rank: number | null;
};

export type ProjectRankingDTO = {
    success: boolean;
    data: { rankings: RankedProject[] };
    error: string | null;
};

export function getRanking() {
    return api.get<ProjectRankingDTO>(`${BASE_URL}/ranking`);
}

export function replaceRankingOrder(projectIds: number[]) {
    return api.putJson<ProjectRankingDTO>(`${BASE_URL}/ranking`, { project_ids: projectIds });
}

export function patchProjectRank(projectId: number, rank: number | null) {
    return api.patchJson<ProjectRankingDTO>(`${BASE_URL}/${projectId}/ranking`, { rank });
}

export function resetRanking() {
    return api.post<ProjectRankingDTO>(`${BASE_URL}/ranking/reset`);
}

// Get Skill Timeline

export type TimelineEventDTO = {
    skill_name: string;
    level: string;
    score: number;
    project_name: string;
    skill_type?: "text" | "code";
};

export type CumulativeSkillDTO = {
    cumulative_score: number;
    projects: string[];
};

export type DateGroupDTO = {
    date: string;
    events: TimelineEventDTO[];
    cumulative_skills: Record<string, CumulativeSkillDTO>;
};

export type CurrentTotalDTO = {
    cumulative_score: number;
    projects: string[];
    skill_type?: "text" | "code";
};

export type TimelineSummaryDTO = {
    total_skills: number;
    total_projects: number;
    date_range: { earliest?: string | null; latest?: string | null };
    skill_names: string[];
};

export type SkillTimelineDTO = {
    dated: DateGroupDTO[];
    undated: TimelineEventDTO[];
    current_totals: Record<string, CurrentTotalDTO>;
    summary: TimelineSummaryDTO;
};

export type SkillTimelineApiResponse = {
    success: boolean;
    data: SkillTimelineDTO;
    error: { message: string; code: number } | null;
};

export function getSkillTimeline() {
    return api.get<SkillTimelineApiResponse>("/skills/timeline");
}

// Project Skill Heatmap (skills x projects)

export type ProjectSkillMatrixDTO = {
    title: string;
    row_labels: string[];
    col_labels: string[];
    matrix: number[][];
};

export function getProjectSkillMatrix(): Promise<ProjectSkillMatrixDTO> {
    return api
        .get<{ success: boolean; data: ProjectSkillMatrixDTO }>("/skills/project-matrix")
        .then((r) => r.data);
}
