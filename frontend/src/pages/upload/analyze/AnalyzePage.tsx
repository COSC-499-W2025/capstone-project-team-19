import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { postUploadRun, type RunPreflightRecord } from "../../../api/uploads";
import { getUsername } from "../../../auth/user";
import UploadWizardShell from "../../../components/UploadWizardShell";
import "../UploadShared.css";

type ScopeName = "individual" | "collaborative";
type ScopeStatus = "pending" | "running" | "completed" | "skipped" | "failed";

type ScopeCard = {
  title: string;
  status: ScopeStatus;
  detail: string;
  progress: number;
};

const INITIAL_CARDS: Record<ScopeName, ScopeCard> = {
  individual: {
    title: "Analyzing individual projects",
    status: "pending",
    detail: "Waiting to start.",
    progress: 0,
  },
  collaborative: {
    title: "Analyzing collaborative projects",
    status: "pending",
    detail: "Waiting to start.",
    progress: 0,
  },
};

const SCOPE_ESTIMATE_SECONDS: Record<ScopeName, number> = {
  individual: 35,
  collaborative: 50,
};

function firstErrorCode(data: RunPreflightRecord): string {
  const first = data.errors?.[0];
  const code = typeof first?.code === "string" ? first.code : "";
  return code || "unknown_error";
}

export default function UploadAnalyzePage() {
  const username = getUsername();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const uploadIdParam = searchParams.get("uploadId") ?? "";
  const uploadId = Number.parseInt(uploadIdParam, 10);
  const hasValidUploadId = Number.isInteger(uploadId) && uploadId > 0;
  const [cards, setCards] = useState<Record<ScopeName, ScopeCard>>(INITIAL_CARDS);
  const [pageMessage, setPageMessage] = useState<string | null>(null);
  const [scopeStartedAt, setScopeStartedAt] = useState<Record<ScopeName, number | null>>({
    individual: null,
    collaborative: null,
  });
  const [clockMs, setClockMs] = useState(() => Date.now());

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "inactive" as const, to: "/upload/upload" },
    { label: "3. Setup", status: "disabled" as const, disabled: true },
    { label: "4. Analyze", status: "active" as const },
  ];

  const setScope = useCallback((scope: ScopeName, patch: Partial<ScopeCard>) => {
    setCards((previous) => ({
      ...previous,
      [scope]: {
        ...previous[scope],
        ...patch,
      },
    }));
  }, []);

  const runScope = useCallback(async (scope: ScopeName): Promise<ScopeStatus> => {
    setScopeStartedAt((previous) => ({ ...previous, [scope]: null }));
    setScope(scope, { status: "running", detail: "Checking readiness...", progress: 30 });

    let check: Awaited<ReturnType<typeof postUploadRun>>;
    try {
      check = await postUploadRun(uploadId, { scope, mode: "check", force_rerun: false });
    } catch {
      setScopeStartedAt((previous) => ({ ...previous, [scope]: null }));
      setScope(scope, { status: "failed", detail: "Readiness check request failed.", progress: 100 });
      return "failed";
    }

    if (!check.success || !check.data) {
      setScopeStartedAt((previous) => ({ ...previous, [scope]: null }));
      setScope(scope, { status: "failed", detail: "Readiness check failed.", progress: 100 });
      return "failed";
    }

    if (!check.data.ready) {
      const code = firstErrorCode(check.data);
      if (code === "no_projects_for_scope") {
        setScopeStartedAt((previous) => ({ ...previous, [scope]: null }));
        setScope(scope, { status: "skipped", detail: "No projects in this scope.", progress: 100 });
        return "skipped";
      }
      if (code === "scope_already_completed") {
        setScopeStartedAt((previous) => ({ ...previous, [scope]: null }));
        setScope(scope, { status: "completed", detail: "Already completed.", progress: 100 });
        return "completed";
      }
      setScopeStartedAt((previous) => ({ ...previous, [scope]: null }));
      setScope(scope, { status: "failed", detail: `Blocked: ${code.replaceAll("_", " ")}`, progress: 100 });
      return "failed";
    }

    const startedAt = Date.now();
    setScopeStartedAt((previous) => ({ ...previous, [scope]: startedAt }));
    setClockMs(startedAt);
    setScope(scope, { status: "running", detail: "Running analysis...", progress: 65 });

    try {
      const run = await postUploadRun(uploadId, { scope, mode: "run", force_rerun: false });
      if (!run.success || !run.data) {
        setScopeStartedAt((previous) => ({ ...previous, [scope]: null }));
        setScope(scope, { status: "failed", detail: "Run failed.", progress: 100 });
        return "failed";
      }
      const warningCount = run.data.warnings?.length ?? 0;
      setScopeStartedAt((previous) => ({ ...previous, [scope]: null }));
      setScope(
        scope,
        {
          status: "completed",
          detail: warningCount > 0 ? `Completed with ${warningCount} warning(s).` : "Completed.",
          progress: 100,
        },
      );
      return "completed";
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Run failed.";
      if (message.includes("scope_already_completed")) {
        setScopeStartedAt((previous) => ({ ...previous, [scope]: null }));
        setScope(scope, { status: "completed", detail: "Already completed.", progress: 100 });
        return "completed";
      }
      setScopeStartedAt((previous) => ({ ...previous, [scope]: null }));
      setScope(scope, { status: "failed", detail: "Run failed.", progress: 100 });
      return "failed";
    }
  }, [setScope, uploadId]);

  useEffect(() => {
    if (!hasValidUploadId) return;

    let active = true;
    async function runSequence() {
      if (!active) return;
      setPageMessage("Running analysis...");
      const individual = await runScope("individual");
      if (!active) return;
      if (individual === "failed") {
        setPageMessage("Analysis stopped: individual scope failed.");
        return;
      }
      const collaborative = await runScope("collaborative");
      if (!active) return;
      if (collaborative === "failed") {
        setPageMessage("Analysis finished with errors.");
        return;
      }
      setPageMessage("Analysis sequence finished.");
    }
    const timeoutId = window.setTimeout(() => {
      void runSequence();
    }, 0);

    return () => {
      active = false;
      window.clearTimeout(timeoutId);
    };
  }, [hasValidUploadId, runScope]);

  const completionText = useMemo(() => {
    if (!pageMessage?.includes("finished")) return null;
    return "All analysis is complete. You can view, manage, and customize results in the Projects or Insights tabs. You can also export them as a resume or portfolio from the Outputs tab.";
  }, [pageMessage]);

  const derivedRunStatus = useMemo(() => {
    const scopeStatuses = [cards.individual.status, cards.collaborative.status];
    if (scopeStatuses.includes("failed")) return "failed";
    if (scopeStatuses.includes("running")) return "analyzing";
    if (scopeStatuses.every((status) => status === "completed" || status === "skipped")) return "done";
    if (scopeStatuses.some((status) => status === "completed" || status === "skipped")) return "analyzing";
    return null;
  }, [cards.collaborative.status, cards.individual.status]);

  useEffect(() => {
    const hasRunningScope = cards.individual.status === "running" || cards.collaborative.status === "running";
    if (!hasRunningScope) return;
    const intervalId = setInterval(() => {
      setClockMs(Date.now());
    }, 700);
    return () => clearInterval(intervalId);
  }, [cards.collaborative.status, cards.individual.status]);

  const progressForScope = useCallback((scope: ScopeName, card: ScopeCard): number => {
    if (card.status !== "running") return card.progress;
    const startedAt = scopeStartedAt[scope];
    if (!startedAt || card.progress < 65) return card.progress;
    const elapsedSeconds = Math.max(0, (clockMs - startedAt) / 1000);
    const estimate = Math.max(1, SCOPE_ESTIMATE_SECONDS[scope]);
    const ratio = Math.min(1, elapsedSeconds / estimate);
    const animated = 65 + ratio * 30;
    return Math.max(card.progress, Math.min(95, Math.round(animated)));
  }, [clockMs, scopeStartedAt]);

  const etaForScope = useCallback((scope: ScopeName, card: ScopeCard): string | null => {
    if (card.status !== "running") return null;
    const startedAt = scopeStartedAt[scope];
    if (!startedAt || card.progress < 65) return "estimating...";
    const elapsedSeconds = Math.max(0, (clockMs - startedAt) / 1000);
    const remaining = Math.max(1, Math.ceil(SCOPE_ESTIMATE_SECONDS[scope] - elapsedSeconds));
    return `${remaining}s remaining`;
  }, [clockMs, scopeStartedAt]);

  function statusLabel(status: ScopeStatus): string {
    if (status === "running") return "In progress";
    if (status === "completed") return "Done";
    if (status === "skipped") return "Skipped";
    if (status === "failed") return "Failed";
    return "Pending";
  }

  return (
    <UploadWizardShell 
      username={username} 
      steps={steps} 
      actionLabel="Analyze" 
      showAction={false}
      breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Upload", href: "/upload" },
          { label: "Analyze", href: "/upload/analyze" },
      ]}
      >
      <div className="max-w-[1040px] space-y-8 rounded-xl bg-[var(--upload-bg)] p-6 max-[980px]:p-4">
        <header>
          <h2 className="text-[18px] leading-normal font-bold text-zinc-900">Analyzing files....</h2>
        </header>

        {!hasValidUploadId && (
          <p className="text-sm text-rose-700">Missing uploadId. Return to Setup and start analysis again.</p>
        )}

        {pageMessage && <p className="text-sm text-zinc-700">{pageMessage}</p>}
        {derivedRunStatus && <p className="text-sm text-zinc-700">Run status: {derivedRunStatus}</p>}

        <section className="space-y-6">
          {(["individual", "collaborative"] as ScopeName[]).map((scope) => {
            const card = cards[scope];
            const displayProgress = progressForScope(scope, card);
            const eta = etaForScope(scope, card);
            return (
              <div key={scope} className="rounded-2xl border border-zinc-300 bg-zinc-50 p-4">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="text-[18px] font-semibold text-zinc-900">{card.title}</p>
                  <p className="text-sm text-zinc-600">{statusLabel(card.status)}</p>
                </div>
                <p className="mb-1 text-sm text-zinc-600">{card.detail}</p>
                {eta && <p className="mb-2 text-xs text-zinc-500">{displayProgress}% • {eta}</p>}
                <div className="h-2 w-full rounded bg-zinc-200">
                  <div
                    className="h-2 rounded bg-[#001166] transition-[width] duration-700 ease-linear"
                    style={{ width: `${displayProgress}%` }}
                  />
                </div>
              </div>
            );
          })}
        </section>

        {completionText && (
          <div className="space-y-4 pt-8">
            <p className="mx-auto max-w-[850px] text-center text-[18px] leading-relaxed text-zinc-900">
              {completionText}
            </p>
            <div className="flex flex-wrap justify-center gap-3">
              <button
                type="button"
                onClick={() => nav("/projects")}
                className="rounded border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-900"
              >
                Go to Projects
              </button>
              <button
                type="button"
                onClick={() => nav("/insights")}
                className="rounded border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-900"
              >
                Go to Insights
              </button>
              <button
                type="button"
                onClick={() => nav("/outputs")}
                className="rounded border border-zinc-300 bg-[#001166] px-4 py-2 text-sm font-medium text-white"
              >
                Go to Outputs
              </button>
            </div>
          </div>
        )}
      </div>
    </UploadWizardShell>
  );
}
