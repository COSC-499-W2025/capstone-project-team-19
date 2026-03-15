import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import type { RunErrorDetail, RunPreflightRecord, RunWarning } from "../../../api/uploads";
import { getUsername } from "../../../auth/user";
import UploadWizardShell from "../../../components/UploadWizardShell";
import "../UploadShared.css";
import SetupAnalyzeConfirmDialog from "./components/SetupAnalyzeConfirmDialog";
import SetupProjectGroup from "./components/SetupProjectGroup";
import { useSetupFlow } from "./hooks/useSetupFlow";
import type { SummaryMode } from "./types";

function asProjectListLabel(value: unknown): string {
  if (Array.isArray(value)) {
    const names = value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
    return names.length > 0 ? names.join(", ") : "selected projects";
  }
  if (typeof value === "string" && value.trim()) return value.trim();
  return "selected projects";
}

function formatRunErrorDetail(item: RunErrorDetail): string {
  const code = String(item.code || "");
  if (code === "upload_not_ready") {
    const status = typeof item.status === "string" && item.status.trim() ? item.status : "unknown";
    return `Upload is not ready yet (status: ${status}).`;
  }
  if (code === "dedup_unresolved") {
    return `Resolve duplicate decisions first for: ${asProjectListLabel(item.projects)}.`;
  }
  if (code === "missing_classifications") {
    return `Missing project mode selection for: ${asProjectListLabel(item.projects)}.`;
  }
  if (code === "unresolved_project_types") {
    return `Missing project type selection for: ${asProjectListLabel(item.projects)}.`;
  }
  if (code === "missing_main_file") {
    const label = asProjectListLabel(item.projects ?? item.project);
    return `Select the main text file for: ${label}.`;
  }
  if (code === "no_projects_for_scope") return "No projects are available for selected scope.";
  if (code === "missing_internal_consent") return "User consent is missing. Please review Step 1.";
  if (code === "already_analyzing") return "Analysis is already running for this upload.";
  if (code === "scope_already_completed") return "This analysis scope was already completed.";
  if (code === "upload_failed") return "This upload is in failed state.";
  return code ? `Blocking issue: ${code}` : "Blocking issue detected.";
}

function formatRunWarning(item: RunWarning): string {
  const code = String(item.code || "");
  if (code === "missing_manual_summary") return "Manual project summary is missing.";
  if (code === "missing_manual_contribution_summary") return "Manual contribution summary is missing.";
  if (code === "missing_key_role") return "Key role is missing.";
  if (code === "missing_github_link") return "GitHub repository is not linked.";
  if (code === "missing_git_identities") return "Collaborative git identity is not selected.";
  if (code === "missing_supporting_files") return "No supporting files selected yet.";
  if (code === "missing_contribution_sections") return "No contribution sections selected yet.";
  if (code === "llm_disabled") return "External LLM consent is not granted; manual-only mode is active.";
  if (code === "drive_not_configured") return "Google Drive is not configured.";
  if (code === "drive_skipped") return "Google Drive is skipped.";
  if (code === "github_not_configured") return "GitHub is not configured.";
  if (code === "github_skipped") return "GitHub connection is skipped.";
  if (code === "missing_drive_links") return "Google Drive links are missing.";
  if (code === "no_git_repo_detected") return "No .git repository detected.";
  return code ? `Non-blocking warning: ${code}` : "Non-blocking warning detected.";
}

function toOptionalBadgeLabel(item: RunWarning): string | null {
  const code = String(item.code || "");
  if (code === "missing_manual_summary") return "missing manual project summary";
  if (code === "missing_manual_contribution_summary") return "missing manual contribution summary";
  if (code === "missing_key_role") return "missing key role";
  if (code === "missing_git_identities") return "missing git identity selection";
  if (code === "missing_supporting_files") return "missing supporting file selection";
  if (code === "missing_contribution_sections") return "missing contribution section selection";
  if (code === "llm_disabled") return "llm disabled";
  if (code === "drive_not_configured" || code === "drive_skipped") return "missing drive connection";
  if (code === "missing_drive_links") return "missing drive file links";
  if (code === "github_not_configured" || code === "github_skipped") return "missing github connection";
  if (code === "no_git_repo_detected") return "no .git detected";
  if (code === "no_git_commits_found") return "no git commits found";
  if (code === "missing_github_link") return null;
  return code ? code.replaceAll("_", " ") : null;
}

type ProjectSummaryModes = {
  project: SummaryMode;
  contribution: SummaryMode;
};

function deriveInitialSummaryModes(args: {
  manualOnlySummaries: boolean;
  manualProjectSummary: string;
  manualContributionSummary: string;
}): ProjectSummaryModes {
  const { manualOnlySummaries } = args;
  if (manualOnlySummaries) {
    return { project: "manual", contribution: "manual" };
  }
  return {
    project: "llm",
    contribution: "llm",
  };
}

export default function UploadSetupPage() {
  const username = getUsername();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const [readiness, setReadiness] = useState<RunPreflightRecord | null>(null);
  const [checkingReadiness, setCheckingReadiness] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [startingAnalysis, setStartingAnalysis] = useState(false);
  const [summaryModesByProject, setSummaryModesByProject] = useState<Record<string, ProjectSummaryModes>>({});

  const uploadIdParam = searchParams.get("uploadId") ?? "";
  const flow = useSetupFlow(uploadIdParam);
  const hasAnalysisStarted = flow.uploadStatus === "analyzing" || flow.uploadStatus === "done";

  useEffect(() => {
    if (flow.hasValidUploadId) return;
    nav("/upload/upload", { replace: true });
  }, [flow.hasValidUploadId, nav]);

  useEffect(() => {
    if (!flow.uploadNotFound) return;
    nav("/upload/upload", { replace: true });
  }, [flow.uploadNotFound, nav]);

  const refreshRunReadiness = useCallback(async () => {
    if (!flow.hasValidUploadId || flow.loading || flow.loadError || flow.projectCards.length === 0 || hasAnalysisStarted) {
      setReadiness(null);
      return null;
    }
    setCheckingReadiness(true);
    const data = await flow.actions.checkRunReadiness("all");
    setCheckingReadiness(false);
    setReadiness(data);
    return data;
  }, [
    flow.actions,
    flow.hasValidUploadId,
    flow.loadError,
    flow.loading,
    flow.projectCards.length,
    hasAnalysisStarted,
  ]);

  useEffect(() => {
    void refreshRunReadiness();
  }, [flow.upload, refreshRunReadiness]);

  useEffect(() => {
    setSummaryModesByProject((previous) => {
      const next: Record<string, ProjectSummaryModes> = {};
      let changed = false;

      for (const project of flow.projectCards) {
        const initialModes = deriveInitialSummaryModes({
          manualOnlySummaries: flow.manualOnlySummaries,
          manualProjectSummary: project.manualProjectSummary,
          manualContributionSummary: project.manualContributionSummary,
        });
        const existing = previous[project.projectName];
        const modes = flow.manualOnlySummaries
          ? { project: "manual" as const, contribution: "manual" as const }
          : existing ?? initialModes;
        next[project.projectName] = modes;
        if (
          !existing ||
          existing.project !== modes.project ||
          existing.contribution !== modes.contribution
        ) {
          changed = true;
        }
      }

      if (!changed && Object.keys(previous).length === Object.keys(next).length) {
        return previous;
      }
      return next;
    });
  }, [flow.manualOnlySummaries, flow.projectCards]);

  const onProjectSummaryModeChange = useCallback((projectName: string, mode: SummaryMode) => {
    setSummaryModesByProject((previous) => {
      const current = previous[projectName] ?? { project: null, contribution: null };
      if (current.project === mode) return previous;
      return {
        ...previous,
        [projectName]: {
          ...current,
          project: mode,
        },
      };
    });
  }, []);

  const onContributionSummaryModeChange = useCallback((projectName: string, mode: SummaryMode) => {
    setSummaryModesByProject((previous) => {
      const current = previous[projectName] ?? { project: null, contribution: null };
      if (current.contribution === mode) return previous;
      return {
        ...previous,
        [projectName]: {
          ...current,
          contribution: mode,
        },
      };
    });
  }, []);

  async function onAnalyzeAction() {
    if (hasAnalysisStarted) {
      nav(`/upload/analyze?uploadId=${uploadIdParam}`);
      return;
    }
    if (hasMissingSummarySelections) return;
    const latestReadiness = await refreshRunReadiness();
    if (!latestReadiness || !latestReadiness.ready) return;
    setConfirmOpen(true);
  }

  async function onConfirmStartAnalysis() {
    setStartingAnalysis(true);
    const data = await flow.actions.runAnalysis("all", false);
    setStartingAnalysis(false);
    if (!data) return;
    setConfirmOpen(false);
    nav(`/upload/analyze?uploadId=${uploadIdParam}`);
  }

  const summaryMissingByProject = useMemo(() => {
    const out: Record<string, boolean> = {};
    for (const project of flow.projectCards) {
      const fallback = deriveInitialSummaryModes({
        manualOnlySummaries: flow.manualOnlySummaries,
        manualProjectSummary: project.manualProjectSummary,
        manualContributionSummary: project.manualContributionSummary,
      });
      const modes = summaryModesByProject[project.projectName] ?? fallback;
      const missing = !flow.manualOnlySummaries && (modes.project === null || modes.contribution === null);
      out[project.projectName] = missing;
    }
    return out;
  }, [flow.manualOnlySummaries, flow.projectCards, summaryModesByProject]);

  const hasMissingSummarySelections = useMemo(
    () => Object.values(summaryMissingByProject).some(Boolean),
    [summaryMissingByProject],
  );

  const analyzeButtonDisabled = useMemo(() => {
    if (!flow.hasValidUploadId) return true;
    if (flow.loading || flow.projectCards.length === 0) return true;
    if (checkingReadiness || startingAnalysis || flow.isMutating) return true;
    if (hasAnalysisStarted) return false;
    if (hasMissingSummarySelections) return true;
    if (!readiness) return true;
    return !readiness.ready;
  }, [
    checkingReadiness,
    flow.hasValidUploadId,
    flow.isMutating,
    flow.loading,
    flow.projectCards.length,
    hasAnalysisStarted,
    hasMissingSummarySelections,
    readiness,
    startingAnalysis,
  ]);

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "inactive" as const, to: "/upload/upload" },
    { label: "3. Setup", status: "active" as const },
    hasAnalysisStarted
      ? { label: "4. Analyze", status: "inactive" as const, to: `/upload/analyze?uploadId=${uploadIdParam}` }
      : { label: "4. Analyze", status: "disabled" as const, disabled: true },
  ];

  if (!flow.hasValidUploadId) return null;

  const blockingErrors = readiness?.errors ?? [];
  const nonBlockingWarnings = readiness?.warnings ?? [];
  const localManualSummaryWarnings = useMemo(() => {
    const out: RunWarning[] = [];
    for (const project of flow.projectCards) {
      const fallback = deriveInitialSummaryModes({
        manualOnlySummaries: flow.manualOnlySummaries,
        manualProjectSummary: project.manualProjectSummary,
        manualContributionSummary: project.manualContributionSummary,
      });
      const modes = summaryModesByProject[project.projectName] ?? fallback;
      if (modes.project === "manual" && project.manualProjectSummary.trim().length === 0) {
        out.push({ code: "missing_manual_summary", project: project.projectName, source: "local" });
      }
      if (modes.contribution === "manual" && project.manualContributionSummary.trim().length === 0) {
        out.push({
          code: "missing_manual_contribution_summary",
          project: project.projectName,
          source: "local",
        });
      }
    }
    return out;
  }, [flow.manualOnlySummaries, flow.projectCards, summaryModesByProject]);

  const effectiveNonBlockingWarnings = useMemo(() => {
    const merged = [...nonBlockingWarnings, ...localManualSummaryWarnings];
    const seen = new Set<string>();
    const out: RunWarning[] = [];
    for (const item of merged) {
      const code = String(item.code || "");
      const projectName = typeof item.project === "string" ? item.project.trim() : "";
      const key = `${projectName}::${code}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(item);
    }
    return out;
  }, [localManualSummaryWarnings, nonBlockingWarnings]);

  const filteredNonBlockingWarnings = useMemo(() => {
    return effectiveNonBlockingWarnings.filter((item) => {
      const code = String(item.code || "");
      const projectName = typeof item.project === "string" ? item.project.trim() : "";
      const summaryModes = summaryModesByProject[projectName];
      if (code === "missing_manual_summary") {
        if (summaryModes?.project === "llm" || summaryModes?.project === null) return false;
      }
      if (code === "missing_manual_contribution_summary") {
        if (summaryModes?.contribution === "llm" || summaryModes?.contribution === null) return false;
      }
      return true;
    });
  }, [effectiveNonBlockingWarnings, summaryModesByProject]);

  const optionalWarningsByProject = useMemo(() => {
    const out: Record<string, string | null> = {};
    for (const item of filteredNonBlockingWarnings) {
      const projectName = typeof item.project === "string" ? item.project.trim() : "";
      if (!projectName) continue;
      if (out[projectName]) continue;
      const label = toOptionalBadgeLabel(item);
      if (!label) continue;
      out[projectName] = label;
    }
    return out;
  }, [filteredNonBlockingWarnings]);

  const warningRows = useMemo(() => {
    const out: RunWarning[] = [];
    const seenProjects = new Set<string>();
    for (const item of filteredNonBlockingWarnings) {
      const projectName = typeof item.project === "string" ? item.project.trim() : "";
      if (!projectName) {
        out.push(item);
        continue;
      }
      if (seenProjects.has(projectName)) continue;
      seenProjects.add(projectName);
      out.push(item);
    }
    return out;
  }, [filteredNonBlockingWarnings]);

  return (
    <>
      <UploadWizardShell
        username={username}
        steps={steps}
        actionLabel={hasAnalysisStarted ? "Open Analyze" : "Analyze"}
        onAction={onAnalyzeAction}
        actionDisabled={analyzeButtonDisabled}
        showAction
      >
        <div className="max-w-[1040px] px-2 pt-5 pb-8 max-[980px]:px-0">

          {flow.loading && <p className="mb-3 text-sm">Loading project setup context...</p>}
          {!flow.loading && !flow.loadError && !hasAnalysisStarted && checkingReadiness && (
            <p className="mb-3 text-sm text-zinc-700">Checking analysis readiness...</p>
          )}
          {flow.loadError && <p className="error mb-3 text-sm">{flow.loadError}</p>}
          {flow.actionError && <p className="error mb-3 text-sm">{flow.actionError}</p>}
          {!flow.loading && !flow.loadError && !hasAnalysisStarted && hasMissingSummarySelections && (
            <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2">
              <p className="mb-1 text-sm font-semibold text-rose-800">
                Analyze is disabled until summary mode is selected for each project.
              </p>
            </div>
          )}
          {!flow.loading && !flow.loadError && !hasAnalysisStarted && readiness && !readiness.ready && blockingErrors.length > 0 && (
            <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2">
              <p className="mb-1 text-sm font-semibold text-rose-800">Analyze is disabled until blocking setup items are resolved.</p>
              <ul className="list-disc space-y-1 pl-5 text-xs text-rose-800">
                {blockingErrors.map((item, index) => (
                  <li key={`${item.code}-${index}`}>{formatRunErrorDetail(item)}</li>
                ))}
              </ul>
            </div>
          )}
          {!flow.loading && !flow.loadError && readiness && warningRows.length > 0 && (
            <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
              <p className="mb-1 text-sm font-semibold text-amber-900">Non-blocking setup warnings</p>
              <ul className="list-disc space-y-1 pl-5 text-xs text-amber-900">
                {warningRows.map((item, index) => (
                  <li key={`${item.code}-${index}`}>
                    {formatRunWarning(item)}
                    {item.project ? ` (${item.project})` : ""}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {!flow.loading && !flow.loadError && flow.projectCards.length === 0 && (
            <p className="mb-3 text-sm">No projects found for this upload.</p>
          )}

          {!flow.loading && !flow.loadError && flow.projectCards.length > 0 && (
            <div className="space-y-8">
              <SetupProjectGroup
                title="Individual Projects"
                projects={flow.individualProjects}
                optionalWarningsByProject={optionalWarningsByProject}
                summaryMissingByProject={summaryMissingByProject}
                summaryModesByProject={summaryModesByProject}
                onProjectSummaryModeChange={onProjectSummaryModeChange}
                onContributionSummaryModeChange={onContributionSummaryModeChange}
                emptyLabel="No individual projects."
                expandedProjectNames={flow.expandedProjectNames}
                onToggleProject={flow.onToggleProject}
                actions={flow.actions}
                isMutating={flow.isMutating}
                manualOnlySummaries={flow.manualOnlySummaries}
              />

              <SetupProjectGroup
                title="Collaborative Projects"
                projects={flow.collaborativeProjects}
                optionalWarningsByProject={optionalWarningsByProject}
                summaryMissingByProject={summaryMissingByProject}
                summaryModesByProject={summaryModesByProject}
                onProjectSummaryModeChange={onProjectSummaryModeChange}
                onContributionSummaryModeChange={onContributionSummaryModeChange}
                emptyLabel="No collaborative projects."
                expandedProjectNames={flow.expandedProjectNames}
                onToggleProject={flow.onToggleProject}
                actions={flow.actions}
                isMutating={flow.isMutating}
                manualOnlySummaries={flow.manualOnlySummaries}
              />
            </div>
          )}
        </div>
      </UploadWizardShell>

      <SetupAnalyzeConfirmDialog
        open={confirmOpen}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={onConfirmStartAnalysis}
        isSubmitting={startingAnalysis}
      />
    </>
  );
}
