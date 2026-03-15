import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
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

function firstErrorCode(data: RunPreflightRecord): string {
  const first = data.errors?.[0];
  const code = typeof first?.code === "string" ? first.code : "";
  return code || "unknown_error";
}

export default function UploadAnalyzePage() {
  const username = getUsername();
  const [searchParams] = useSearchParams();
  const uploadIdParam = searchParams.get("uploadId") ?? "";
  const uploadId = Number.parseInt(uploadIdParam, 10);
  const hasValidUploadId = Number.isInteger(uploadId) && uploadId > 0;
  const [cards, setCards] = useState<Record<ScopeName, ScopeCard>>(INITIAL_CARDS);
  const [pageMessage, setPageMessage] = useState<string | null>(null);
  const startedRef = useRef(false);

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

  const runScope = useCallback(async (scope: ScopeName) => {
    setScope(scope, { status: "running", detail: "Checking readiness...", progress: 30 });

    const check = await postUploadRun(uploadId, { scope, mode: "check", force_rerun: false });
    if (!check.success || !check.data) {
      setScope(scope, { status: "failed", detail: "Readiness check failed.", progress: 100 });
      return;
    }

    if (!check.data.ready) {
      const code = firstErrorCode(check.data);
      if (code === "no_projects_for_scope") {
        setScope(scope, { status: "skipped", detail: "No projects in this scope.", progress: 100 });
        return;
      }
      if (code === "scope_already_completed") {
        setScope(scope, { status: "completed", detail: "Already completed.", progress: 100 });
        return;
      }
      setScope(scope, { status: "failed", detail: `Blocked: ${code.replaceAll("_", " ")}`, progress: 100 });
      return;
    }

    setScope(scope, { status: "running", detail: "Running analysis...", progress: 65 });

    try {
      const run = await postUploadRun(uploadId, { scope, mode: "run", force_rerun: false });
      if (!run.success || !run.data) {
        setScope(scope, { status: "failed", detail: "Run failed.", progress: 100 });
        return;
      }
      const warningCount = run.data.warnings?.length ?? 0;
      setScope(
        scope,
        {
          status: "completed",
          detail: warningCount > 0 ? `Completed with ${warningCount} warning(s).` : "Completed.",
          progress: 100,
        },
      );
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Run failed.";
      if (message.includes("scope_already_completed")) {
        setScope(scope, { status: "completed", detail: "Already completed.", progress: 100 });
        return;
      }
      setScope(scope, { status: "failed", detail: "Run failed.", progress: 100 });
    }
  }, [setScope, uploadId]);

  useEffect(() => {
    if (!hasValidUploadId) return;
    if (startedRef.current) return;
    startedRef.current = true;

    let active = true;
    async function runSequence() {
      setPageMessage("Running analysis...");
      await runScope("individual");
      if (!active) return;
      await runScope("collaborative");
      if (!active) return;
      setPageMessage("Analysis sequence finished.");
    }
    runSequence();

    return () => {
      active = false;
    };
  }, [hasValidUploadId, runScope]);

  const completionText = useMemo(() => {
    if (!pageMessage?.includes("finished")) return null;
    return "All analysis is complete. You can view, manage, and customize results in the Projects or Insights tabs. You can also export them as a resume or portfolio from the Outputs tab.";
  }, [pageMessage]);

  function statusLabel(status: ScopeStatus): string {
    if (status === "running") return "In progress";
    if (status === "completed") return "Done";
    if (status === "skipped") return "Skipped";
    if (status === "failed") return "Failed";
    return "Pending";
  }

  return (
    <UploadWizardShell username={username} steps={steps} actionLabel="Analyze" showAction={false}>
      <div className="max-w-[1040px] space-y-8 rounded-xl bg-[var(--upload-bg)] p-6 max-[980px]:p-4">
        <header>
          <h2 className="text-4xl leading-tight font-semibold text-zinc-900">Analyzing files....</h2>
        </header>

        {pageMessage && <p className="text-sm text-zinc-700">{pageMessage}</p>}

        <section className="space-y-6">
          {(["individual", "collaborative"] as ScopeName[]).map((scope) => {
            const card = cards[scope];
            return (
              <div key={scope} className="rounded-2xl border border-zinc-300 bg-zinc-50 p-4">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="text-lg font-semibold text-zinc-900">{card.title}</p>
                  <p className="text-sm text-zinc-600">{statusLabel(card.status)}</p>
                </div>
                <p className="mb-3 text-sm text-zinc-600">{card.detail}</p>
                <div className="h-2 w-full rounded bg-zinc-200">
                  <div className="h-2 rounded bg-black" style={{ width: `${card.progress}%` }} />
                </div>
              </div>
            );
          })}
        </section>

        {completionText && (
          <p className="mx-auto max-w-[850px] pt-8 text-center text-3xl leading-snug text-zinc-900 max-[980px]:text-base">
            {completionText}
          </p>
        )}
      </div>
    </UploadWizardShell>
  );
}
