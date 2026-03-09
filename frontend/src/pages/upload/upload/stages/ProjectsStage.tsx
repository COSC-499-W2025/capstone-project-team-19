type Props = {
  discoveredProjects: string[];
  projectNotes: Record<string, string[]>;
  allProjectsPreviouslySkipped: boolean;
};

export default function ProjectsStage({ discoveredProjects, projectNotes, allProjectsPreviouslySkipped }: Props) {
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
              {projectNotes[projectName]?.map((note) => (
                <div key={`${projectName}-${note}`} className="projectsStageListNote">
                  {note}
                </div>
              ))}
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
