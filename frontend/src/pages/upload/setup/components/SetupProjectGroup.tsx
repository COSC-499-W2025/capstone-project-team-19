import type { SetupProjectCard as SetupProjectCardModel } from "../types";
import SetupProjectCard from "./SetupProjectCard";

type Props = {
  title: string;
  projects: SetupProjectCardModel[];
  emptyLabel: string;
  expandedProjectName: string | null;
  onToggleProject: (projectName: string) => void;
};

export default function SetupProjectGroup({
  title,
  projects,
  emptyLabel,
  expandedProjectName,
  onToggleProject,
}: Props) {
  return (
    <section className="setupGroupBlock">
      <h3 className="setupGroupTitle">{title}</h3>
      <div className="setupGroupList">
        {projects.length === 0 && <div className="setupGroupEmpty">{emptyLabel}</div>}
        {projects.map((project) => (
          <SetupProjectCard
            key={project.projectName}
            project={project}
            expanded={expandedProjectName === project.projectName}
            onToggle={onToggleProject}
          />
        ))}
      </div>
    </section>
  );
}
