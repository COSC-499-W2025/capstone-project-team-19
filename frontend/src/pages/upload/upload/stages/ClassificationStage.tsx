import type { ProjectClassificationValue, ProjectTypeValue } from "../uploadTypes";
import { toProjectClassificationValue, toProjectTypeValue } from "../uploadHelpers";

type Props = {
  classificationProjectsForDisplay: string[];
  completedClassificationCount: number;
  classifications: Record<string, ProjectClassificationValue>;
  projectTypes: Record<string, ProjectTypeValue>;
  autoAssignments: Record<string, string>;
  autoDetectedProjectTypes: Record<string, "code" | "text">;
  existingClassifications: Record<string, string>;
  existingProjectTypes: Record<string, string>;
  onClassificationChange: (projectName: string, value: ProjectClassificationValue) => void;
  onProjectTypeChange: (projectName: string, value: ProjectTypeValue) => void;
};

export default function ClassificationStage({
  classificationProjectsForDisplay,
  completedClassificationCount,
  classifications,
  projectTypes,
  autoAssignments,
  autoDetectedProjectTypes,
  existingClassifications,
  existingProjectTypes,
  onClassificationChange,
  onProjectTypeChange,
}: Props) {
  return (
    <div className="classificationStagePanel">
      <h2 className="wizardPlaceholderTitle">Classification and Type</h2>
      <p className="wizardPlaceholderText">Review all projects and choose classification and project type.</p>

      {classificationProjectsForDisplay.length === 0 ? (
        <div className="uploadEmptyState">No projects found.</div>
      ) : (
        <>
          <div className="classificationStageMeta">
            {completedClassificationCount} of {classificationProjectsForDisplay.length} completed
          </div>

          <div className="classificationStageTableWrap">
            <table className="classificationStageTable">
              <thead>
                <tr>
                  <th>Projects</th>
                  <th>Classification</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {classificationProjectsForDisplay.map((projectName) => (
                  <tr key={projectName}>
                    <td>{projectName}</td>
                    <td>
                      <select
                        className="classificationStageSelect"
                        value={toProjectClassificationValue(
                          classifications[projectName] ?? autoAssignments[projectName] ?? existingClassifications[projectName],
                        )}
                        onChange={(event) => onClassificationChange(projectName, event.target.value as ProjectClassificationValue)}
                      >
                        <option value="">Select</option>
                        <option value="individual">Individual</option>
                        <option value="collaborative">Collaborative</option>
                      </select>
                    </td>
                    <td>
                      <select
                        className="classificationStageSelect"
                        value={toProjectTypeValue(
                          projectTypes[projectName] ??
                            autoDetectedProjectTypes[projectName] ??
                            existingProjectTypes[projectName],
                        )}
                        onChange={(event) => onProjectTypeChange(projectName, event.target.value as ProjectTypeValue)}
                      >
                        <option value="">Select</option>
                        <option value="text">Text</option>
                        <option value="code">Code</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
