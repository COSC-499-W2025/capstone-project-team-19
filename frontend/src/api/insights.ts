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