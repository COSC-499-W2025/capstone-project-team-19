type Props = {
  discoveredProjects: string[];
  projectNotes: Record<string, string[]>;
};

export default function ProjectsStage({ discoveredProjects, projectNotes }: Props) {
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
    </div>
  );
}
