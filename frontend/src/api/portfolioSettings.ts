import { api } from "./client";

interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: { message: string; code: number } | null;
}

export interface PortfolioSettings {
  portfolio_public: boolean;
  active_resume_id: number | null;
}

export function getPortfolioSettings(): Promise<PortfolioSettings> {
  return api
    .get<ApiResponse<PortfolioSettings>>("/portfolio-settings")
    .then((r) => r.data ?? { portfolio_public: false, active_resume_id: null });
}

export function updatePortfolioSettings(settings: {
  portfolio_public?: boolean;
  active_resume_id?: number | null;
  clear_active_resume?: boolean;
}): Promise<PortfolioSettings> {
  return api
    .putJson<ApiResponse<PortfolioSettings>>("/portfolio-settings", settings)
    .then((r) => r.data ?? { portfolio_public: false, active_resume_id: null });
}

export function updateProjectVisibility(
  projectSummaryId: number,
  isPublic: boolean,
): Promise<void> {
  return api
    .patchJson<ApiResponse<unknown>>(
      `/portfolio-settings/projects/${projectSummaryId}/visibility`,
      { is_public: isPublic },
    )
    .then(() => undefined);
}
