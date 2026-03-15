import { ChevronDown, ChevronRight } from "lucide-react";
import { toProjectTypeLabel } from "../selectors";
import type { SetupProjectCard as SetupProjectCardModel } from "../types";
import ContributionSummarySection from "./sections/ContributionSummarySection";
import ManualSummarySection from "./sections/ManualSummarySection";
import ProjectSetupInputsSection from "./sections/ProjectSetupInputsSection";

type Props = {
  project: SetupProjectCardModel;
  expanded: boolean;
  onToggle: (projectName: string) => void;
};

export default function SetupProjectCard({ project, expanded, onToggle }: Props) {
  return (
    <article className="setupProjectCard">
      <button
        type="button"
        className="setupProjectCardHeader"
        onClick={() => onToggle(project.projectName)}
      >
        <div className="setupProjectCardHeadLeft">
          <span className="setupProjectTitle">
            {project.projectName} | {toProjectTypeLabel(project.projectType)}
          </span>
          <span className={`setupStatusPill setupStatusPill--${project.statusTone}`}>
            {project.statusLabel}
          </span>
        </div>
        {expanded ? <ChevronDown size={18} aria-hidden="true" /> : <ChevronRight size={18} aria-hidden="true" />}
      </button>

      {expanded && (
        <div className="setupProjectCardBody">
          <ManualSummarySection />
          <ContributionSummarySection />
          <ProjectSetupInputsSection collaborative={project.classification === "collaborative"} />
          {project.projectKey && <p className="setupProjectMeta">Project key: {project.projectKey}</p>}
        </div>
      )}
    </article>
  );
}
