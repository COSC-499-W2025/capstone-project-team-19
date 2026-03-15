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
    <section className="space-y-3">
      <h3 className="m-0 text-[2rem] leading-none font-extrabold tracking-tight text-zinc-900">{title}</h3>
      <div className="space-y-3">
        {projects.length === 0 && (
          <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 px-4 py-3 text-sm text-zinc-600">
            {emptyLabel}
          </div>
        )}
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
