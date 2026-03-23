import type { ProjectNote } from "../uploadTypes";

type Props = {
  discoveredProjects: string[];
  projectNotes: Record<string, ProjectNote[]>;
  allProjectsPreviouslySkipped: boolean;
  onOpenProjectDetailsInNewTab: (projectName: string) => void;
};

export default function ProjectsStage({
  discoveredProjects,
  projectNotes,
  allProjectsPreviouslySkipped,
  onOpenProjectDetailsInNewTab,
}: Props) {
  return (
    <div className="projectsStagePanel">
      <h2 className="wizardPlaceholderTitle">Projects</h2>
      <p className="wizardPlaceholderText">Parsed projects from this ZIP are shown before deduplication.</p>

      {discoveredProjects.length === 0 ? (
        <div className="uploadEmptyState">No projects found.</div>
      ) : (
        <ul className="projectsStageList">
          {discoveredProjects.map((projectName) => (
            <li key={projectName} className="projectsStageListItem">
              <div>{projectName}</div>
              {projectNotes[projectName]?.map((note) => {
                if (!note.linkedProjectName) {
                  return (
                    <div key={`${projectName}-${note.text}`} className="projectsStageListNote">
                      {note.text}
                    </div>
                  );
                }

                return (
                  <div key={`${projectName}-${note.text}`} className="projectsStageListNote">
                    <span>{note.text} </span>
                    <button
                      type="button"
                      className="projectsStageListNoteLink"
                      onClick={() => onOpenProjectDetailsInNewTab(note.linkedProjectName ?? "")}
                    >
                      See project: "{note.linkedProjectName}"
                    </button>
                  </div>
                );
              })}
            </li>
          ))}
        </ul>
      )}

      {allProjectsPreviouslySkipped && (
        <p className="wizardPlaceholderText projectsStageBlockedNote">
          You cannot continue because all detected projects were already analyzed in previous uploads.
        </p>
      )}
    </div>
  );
}
