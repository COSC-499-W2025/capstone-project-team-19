import { api } from "./client";

// Get Project Ranking (returns a list of all projects in their ranked order)

export type RankedProject = {
    rank: number;
    project_summary_id: number;
    project_name: string;
    score: number;
    manual_rank: number | null;
};

type RankingResponse = {
    success: Boolean;
    data: {
        rankings: RankedProject[];
    };
    error: string | null;
};

export async function getProjectRanking() {
    const res = await api.get<RankingResponse>("/projects/ranking");
    return res.data.rankings;
}