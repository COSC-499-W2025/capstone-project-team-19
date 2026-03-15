import type { SetupFlowResult, SetupProjectCard as SetupProjectCardModel, SummaryMode } from "../types";
import SetupProjectCard from "./SetupProjectCard";

type Props = {
  title: string;
  projects: SetupProjectCardModel[];
  optionalWarningsByProject: Record<string, string | null>;
  summaryMissingByProject: Record<string, boolean>;
  summaryModesByProject: Record<string, { project: SummaryMode; contribution: SummaryMode }>;
  onProjectSummaryModeChange: (projectName: string, mode: SummaryMode) => void;
  onContributionSummaryModeChange: (projectName: string, mode: SummaryMode) => void;
  emptyLabel: string;
  expandedProjectNames: string[];
  onToggleProject: (projectName: string) => void;
  actions: SetupFlowResult["actions"];
  isMutating: boolean;
  manualOnlySummaries: boolean;
};

export default function SetupProjectGroup({
  title,
  projects,
  optionalWarningsByProject,
  summaryMissingByProject,
  summaryModesByProject,
  onProjectSummaryModeChange,
  onContributionSummaryModeChange,
  emptyLabel,
  expandedProjectNames,
  onToggleProject,
  actions,
  isMutating,
  manualOnlySummaries,
}: Props) {
  return (
    <section className="space-y-4">
      <h3 className="m-0 text-[1.8rem] leading-none font-extrabold tracking-tight text-zinc-900">{title}</h3>
      <div className="space-y-4">
        {projects.length === 0 && (
          <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 px-5 py-4 text-base text-zinc-600">
            {emptyLabel}
          </div>
        )}
        {projects.map((project) => (
          <SetupProjectCard
            key={project.projectName}
            project={project}
            optionalWarningLabel={optionalWarningsByProject[project.projectName] ?? null}
            summaryMissing={summaryMissingByProject[project.projectName] ?? false}
            projectSummaryMode={summaryModesByProject[project.projectName]?.project ?? null}
            contributionSummaryMode={summaryModesByProject[project.projectName]?.contribution ?? null}
            onProjectSummaryModeChange={onProjectSummaryModeChange}
            onContributionSummaryModeChange={onContributionSummaryModeChange}
            expanded={expandedProjectNames.includes(project.projectName)}
            onToggle={onToggleProject}
            actions={actions}
            isMutating={isMutating}
            manualOnlySummaries={manualOnlySummaries}
          />
        ))}
      </div>
    </section>
  );
}
