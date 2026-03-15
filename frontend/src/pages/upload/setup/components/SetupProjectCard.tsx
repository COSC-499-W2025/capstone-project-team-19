import { ChevronDown, ChevronRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { toProjectTypeLabel } from "../selectors";
import type { SetupFlowResult, SetupProjectCard as SetupProjectCardModel } from "../types";
import CodeSetupSection from "./sections/CodeSetupSection";
import ContributionSummarySection from "./sections/ContributionSummarySection";
import ManualSummarySection from "./sections/ManualSummarySection";
import ProjectSetupInputsSection from "./sections/ProjectSetupInputsSection";
import TextSetupSection from "./sections/TextSetupSection";

type Props = {
  project: SetupProjectCardModel;
  expanded: boolean;
  onToggle: (projectName: string) => void;
  actions: SetupFlowResult["actions"];
  isMutating: boolean;
};

export default function SetupProjectCard({ project, expanded, onToggle, actions, isMutating }: Props) {
  const badgeToneClass = {
    ready: "border-emerald-200 bg-emerald-50 text-emerald-700",
    warning: "border-rose-200 bg-rose-50 text-rose-700",
    neutral: "border-zinc-200 bg-zinc-100 text-zinc-600",
  }[project.statusTone];

  const badgeDotClass = {
    ready: "bg-emerald-500",
    warning: "bg-rose-500",
    neutral: "bg-zinc-500",
  }[project.statusTone];

  return (
    <Card className="gap-0 rounded-lg border border-zinc-300 bg-white py-0 shadow-none ring-0">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition-colors hover:bg-zinc-50"
        onClick={() => onToggle(project.projectName)}
      >
        <div className="flex min-w-0 items-center gap-3 max-sm:flex-col max-sm:items-start max-sm:gap-2">
          <span className="truncate text-sm font-medium text-zinc-900 max-sm:whitespace-normal">
            {project.projectName} | {toProjectTypeLabel(project.projectType)}
          </span>
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium whitespace-nowrap",
              badgeToneClass,
            )}
          >
            <span className={cn("size-1.5 rounded-full", badgeDotClass)} />
            {project.statusLabel}
          </span>
        </div>
        {expanded ? <ChevronDown size={18} aria-hidden="true" className="text-zinc-700" /> : <ChevronRight size={18} aria-hidden="true" className="text-zinc-700" />}
      </button>

      {expanded && (
        <CardContent className="space-y-3 border-t border-zinc-200 bg-zinc-50 px-4 py-4">
          <ManualSummarySection />
          <ContributionSummarySection />
          {project.projectType === "code" ? (
            <CodeSetupSection project={project} actions={actions} isMutating={isMutating} />
          ) : project.projectType === "text" ? (
            <TextSetupSection project={project} actions={actions} isMutating={isMutating} />
          ) : (
            <ProjectSetupInputsSection collaborative={project.classification === "collaborative"} />
          )}
          {project.projectKey && <p className="text-xs text-zinc-600">Project key: {project.projectKey}</p>}
        </CardContent>
      )}
    </Card>
  );
}
