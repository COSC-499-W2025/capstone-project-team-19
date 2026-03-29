import { ChevronDown, ChevronRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { toProjectTypeLabel } from "../selectors";
import type { SetupFlowResult, SetupProjectCard as SetupProjectCardModel, SummaryMode } from "../types";
import CodeSetupSection from "./sections/CodeSetupSection";
import ContributionSummarySection from "./sections/ContributionSummarySection";
import KeyRoleSection from "./sections/KeyRoleSection";
import ManualSummarySection from "./sections/ManualSummarySection";
import ProjectSetupInputsSection from "./sections/ProjectSetupInputsSection";
import TextSetupSection from "./sections/TextSetupSection";

type Props = {
  project: SetupProjectCardModel;
  optionalWarningLabel: string | null;
  summaryMissing: boolean;
  projectSummaryMode: SummaryMode;
  contributionSummaryMode: SummaryMode;
  onProjectSummaryModeChange: (projectName: string, mode: SummaryMode) => void;
  onContributionSummaryModeChange: (projectName: string, mode: SummaryMode) => void;
  expanded: boolean;
  onToggle: (projectName: string) => void;
  actions: SetupFlowResult["actions"];
  isMutating: boolean;
  manualOnlySummaries: boolean;
};

export default function SetupProjectCard({
  project,
  optionalWarningLabel,
  summaryMissing,
  projectSummaryMode,
  contributionSummaryMode,
  onProjectSummaryModeChange,
  onContributionSummaryModeChange,
  expanded,
  onToggle,
  actions,
  isMutating,
  manualOnlySummaries,
}: Props) {
  const statusTone = summaryMissing ? "warning" : project.statusTone;
  const statusLabel = summaryMissing ? "Missing summary" : project.statusLabel;

  const badgeToneClass = {
    ready: "border-emerald-200 bg-emerald-50 text-emerald-700",
    warning: "border-rose-200 bg-rose-50 text-rose-700",
    neutral: "border-zinc-200 bg-zinc-100 text-zinc-600",
  }[statusTone];

  const badgeDotClass = {
    ready: "bg-emerald-500",
    warning: "bg-rose-500",
    neutral: "bg-zinc-500",
  }[statusTone];

  const optionalBadgeClass = "border-amber-200 bg-amber-50 text-amber-700";
  const optionalBadgeDotClass = "bg-amber-500";

  return (
    <Card className="gap-0 rounded-md border border-zinc-400 bg-white py-0 shadow-none ring-0">
      <button
        type="button"
        className="flex min-h-[60px] w-full items-center justify-between gap-4 px-8 py-3 text-left transition-colors hover:bg-zinc-50"
        onClick={() => onToggle(project.projectName)}
      >
        <div className="flex min-w-0 items-center gap-3 max-sm:flex-col max-sm:items-start max-sm:gap-2">
          <span className="truncate text-base font-medium text-zinc-900 max-sm:whitespace-normal">
            {project.projectName} | {toProjectTypeLabel(project.projectType)}
          </span>
          <div className="flex items-center gap-2 max-sm:flex-wrap">
            <span
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-medium whitespace-nowrap",
                badgeToneClass,
              )}
            >
              <span className={cn("size-1.5 rounded-full", badgeDotClass)} />
              {statusLabel}
            </span>
            {optionalWarningLabel && (
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-medium whitespace-nowrap",
                  optionalBadgeClass,
                )}
              >
                <span className={cn("size-1.5 rounded-full", optionalBadgeDotClass)} />
                {optionalWarningLabel}
              </span>
            )}
          </div>
        </div>
        {expanded ? <ChevronDown size={18} aria-hidden="true" className="text-zinc-700" /> : <ChevronRight size={18} aria-hidden="true" className="text-zinc-700" />}
      </button>

      {expanded && (
        <CardContent className="space-y-5 border-t border-zinc-300 bg-zinc-100 px-8 py-6">
          <ManualSummarySection
            project={project}
            actions={actions}
            isMutating={isMutating}
            manualOnlySummaries={manualOnlySummaries}
            mode={projectSummaryMode}
            onModeChange={(mode) => onProjectSummaryModeChange(project.projectName, mode)}
          />
          <ContributionSummarySection
            project={project}
            actions={actions}
            isMutating={isMutating}
            manualOnlySummaries={manualOnlySummaries}
            mode={contributionSummaryMode}
            onModeChange={(mode) => onContributionSummaryModeChange(project.projectName, mode)}
          />
          <KeyRoleSection project={project} actions={actions} isMutating={isMutating} manualOnlySummaries={manualOnlySummaries}/>
          {project.projectType === "code" ? (
            <CodeSetupSection project={project} actions={actions} isMutating={isMutating} />
          ) : project.projectType === "text" ? (
            <TextSetupSection project={project} actions={actions} isMutating={isMutating} />
          ) : (
            <ProjectSetupInputsSection collaborative={project.classification === "collaborative"} />
          )}
        </CardContent>
      )}
    </Card>
  );
}
