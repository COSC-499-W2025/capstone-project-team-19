import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { getUsername } from "../auth/user";
import UploadWizardShell from "../components/UploadWizardShell";

type UploadFlowStage = "upload" | "projects" | "deduplication" | "classification";

type StageDef = {
  key: UploadFlowStage;
  label: string;
};

type DedupDecisionValue = "new_project" | "new_version";
type ProjectClassificationValue = "" | "individual" | "collaborative";
type ProjectTypeValue = "" | "text" | "code";

type DedupCase = {
  projectName: string;
  existingProjectName: string;
  similarityLabel: string;
  pathLabel: string;
  filesLabel: string;
};

type MockWizardScenario = "default" | "no_dedup" | "no_projects";

type MockWizardData = {
  scenario: MockWizardScenario;
  projects: string[];
  dedupCases: DedupCase[];
};

const STAGES: StageDef[] = [
  { key: "upload", label: "Upload" },
  { key: "projects", label: "Projects" },
  { key: "deduplication", label: "Deduplication" },
  { key: "classification", label: "Classification" },
];

function deriveMockWizardData(file: File | null): MockWizardData {
  if (!file) {
    return { scenario: "default", projects: [], dedupCases: [] };
  }

  const fileName = file.name.toLowerCase();
  const scenario: MockWizardScenario = fileName.includes("empty")
    ? "no_projects"
    : fileName.includes("nodedup")
      ? "no_dedup"
      : "default";

  if (scenario === "no_projects") {
    return {
      scenario,
      projects: [],
      dedupCases: [],
    };
  }

  const projects = ["ProjectsA", "ProjectsB", "ProjectsC"];

  if (scenario === "no_dedup") {
    return {
      scenario,
      projects,
      dedupCases: [],
    };
  }

  return {
    scenario,
    projects,
    dedupCases: [
      {
        projectName: "ProjectsB",
        existingProjectName: "ProjectsLegacyB",
        similarityLabel: "75% match",
        pathLabel: "Path 75% similar",
        filesLabel: "4 files",
      },
      {
        projectName: "ProjectsC",
        existingProjectName: "ProjectsLegacyC",
        similarityLabel: "72% match",
        pathLabel: "Path 72% similar",
        filesLabel: "6 files",
      },
    ],
  };
}

function stageIndexByKey(key: UploadFlowStage): number {
  return STAGES.findIndex((stage) => stage.key === key);
}

function nextStageIndex(fromKey: UploadFlowStage): number {
  if (fromKey === "upload") return stageIndexByKey("projects");
  if (fromKey === "projects") return stageIndexByKey("deduplication");
  if (fromKey === "deduplication") return stageIndexByKey("classification");
  return stageIndexByKey("classification");
}

export default function UploadPage() {
  const username = getUsername();

  const [stageIndex, setStageIndex] = useState(0);
  const [maxUnlockedStageIndex, setMaxUnlockedStageIndex] = useState(0);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const [dedupCaseIndex, setDedupCaseIndex] = useState(0);
  const [dedupDecisions, setDedupDecisions] = useState<Record<string, DedupDecisionValue>>({});

  const [classificationIndex, setClassificationIndex] = useState(0);
  const [classifications, setClassifications] = useState<Record<string, ProjectClassificationValue>>({});
  const [projectTypes, setProjectTypes] = useState<Record<string, ProjectTypeValue>>({});

  const uploadInputRef = useRef<HTMLInputElement | null>(null);

  const currentStage = useMemo(() => STAGES[stageIndex], [stageIndex]);
  const canGoBack = stageIndex > 0;

  const mockWizardData = useMemo(() => deriveMockWizardData(selectedFile), [selectedFile]);
  const projectsPreview = mockWizardData.projects;
  const dedupPreview = mockWizardData.dedupCases;

  const currentDedupCase = dedupPreview[dedupCaseIndex] ?? null;
  const canGoToPreviousDedupCase = dedupCaseIndex > 0;
  const canGoToNextDedupCase = dedupCaseIndex < dedupPreview.length - 1;

  const currentClassificationProject = projectsPreview[classificationIndex] ?? null;
  const canGoToPreviousClassificationProject = classificationIndex > 0;
  const canGoToNextClassificationProject = classificationIndex < projectsPreview.length - 1;

  const completedClassificationCount = useMemo(
    () =>
      projectsPreview.filter((projectName) => Boolean(classifications[projectName]) && Boolean(projectTypes[projectName]))
        .length,
    [classifications, projectTypes, projectsPreview],
  );

  const isDedupComplete = useMemo(
    () => dedupPreview.length === 0 || dedupPreview.every((entry) => Boolean(dedupDecisions[entry.projectName])),
    [dedupDecisions, dedupPreview],
  );

  const isClassificationComplete = useMemo(
    () =>
      projectsPreview.length > 0 &&
      projectsPreview.every((projectName) => Boolean(classifications[projectName]) && Boolean(projectTypes[projectName])),
    [classifications, projectTypes, projectsPreview],
  );

  const actionLabel = currentStage.key === "classification" ? "Finish" : "Next";
  const actionDisabled = useMemo(() => {
    if (currentStage.key === "upload") return !selectedFile;
    if (currentStage.key === "deduplication") return !isDedupComplete;
    if (currentStage.key === "classification") return !isClassificationComplete;
    return false;
  }, [currentStage.key, isClassificationComplete, isDedupComplete, selectedFile]);

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "active" as const },
    { label: "3. Setup", status: "disabled" as const, disabled: true },
  ];

  const sizeLabel = selectedFile ? `${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB` : null;

  useEffect(() => {
    setDedupCaseIndex(0);
    setDedupDecisions({});

    setClassificationIndex(0);
    setClassifications({});
    setProjectTypes({});

    setStageIndex(0);
    setMaxUnlockedStageIndex(0);
  }, [selectedFile]);

  useEffect(() => {
    if (dedupCaseIndex <= dedupPreview.length - 1) return;
    setDedupCaseIndex(0);
  }, [dedupCaseIndex, dedupPreview.length]);

  useEffect(() => {
    if (classificationIndex <= projectsPreview.length - 1) return;
    setClassificationIndex(0);
  }, [classificationIndex, projectsPreview.length]);

  function onNext() {
    if (actionDisabled) return;
    if (currentStage.key === "classification") return;

    const targetStageIndex = nextStageIndex(currentStage.key);
    setStageIndex(targetStageIndex);
    setMaxUnlockedStageIndex((prev) => Math.max(prev, targetStageIndex));
  }

  function onBack() {
    if (!canGoBack) return;
    setStageIndex((prev) => prev - 1);
  }

  function handleFileSelect(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0] ?? null;
    if (!file) return;
    setSelectedFile(file);
  }

  function renderUploadStage() {
    return (
      <div className="uploadStagePanel">
        <h2 className="wizardPlaceholderTitle">Upload Placeholder</h2>

        <div className="uploadIntroRow">
          <div className="uploadIntroText">
            <p>
              We treat each folder as one project. Optionally, organize projects under <code>individual/</code> and{" "}
              <code>collaborative/</code> before zipping.
            </p>
            <p>
              Upload accepts one ZIP file for now. Deduplication and classification are shown in later stages in this
              flow.
            </p>
            <p className="uploadScenarioLine">
              Mock scenario:{" "}
              <strong>
                {mockWizardData.scenario === "default" && "default"}
                {mockWizardData.scenario === "no_dedup" && "no deduplication"}
                {mockWizardData.scenario === "no_projects" && "no projects"}
              </strong>
              . Use filename containing <code>nodedup</code> or <code>empty</code> to switch behavior.
            </p>
          </div>

          <div className="uploadStructureCard" aria-label="Upload structure example">
            <div>projects.zip</div>
            <div>individual/</div>
            <div>ProjectA/</div>
            <div>ProjectB/</div>
            <div>collaborative/</div>
            <div>ProjectC/</div>
          </div>
        </div>

        <input
          ref={uploadInputRef}
          type="file"
          accept=".zip,application/zip"
          className="uploadFileInput"
          onChange={handleFileSelect}
        />

        <div
          className={`uploadDropZone${dragActive ? " uploadDropZone--active" : ""}`}
          onDragOver={(event) => {
            event.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
        >
          <div className="uploadDropLeft">
            <div className="uploadDropTitle">Select a file or drag and drop here</div>
            <div className="uploadDropHint">ZIP file only</div>
          </div>

          <button type="button" className="uploadSelectBtn" onClick={() => uploadInputRef.current?.click()}>
            SELECT FILE
          </button>
        </div>

        <div className="uploadFileAddedBlock">
          <h3 className="uploadFileAddedTitle">File added</h3>
          {selectedFile ? (
            <div className="uploadFileRow">
              <span className="uploadFileName">{selectedFile.name}</span>
              <span className="uploadFileSize">{sizeLabel}</span>
            </div>
          ) : (
            <div className="uploadFileEmpty">No file selected yet.</div>
          )}
        </div>
      </div>
    );
  }

  function renderProjectsStage() {
    return (
      <div className="projectsStagePanel">
        <h2 className="wizardPlaceholderTitle">Projects</h2>
        <p className="wizardPlaceholderText">Parsed projects from the uploaded ZIP are shown here before deduplication.</p>

        {projectsPreview.length === 0 ? (
          <div className="uploadEmptyState">No projects found.</div>
        ) : (
          <ul className="projectsStageList">
            {projectsPreview.map((projectName) => (
              <li key={projectName} className="projectsStageListItem">
                {projectName}
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  function renderDedupStage() {
    return (
      <div className="dedupStagePanel">
        <h2 className="wizardPlaceholderTitle">Deduplication</h2>
        <p className="wizardPlaceholderText">Review similar projects one-by-one and choose how each should be treated.</p>

        {dedupPreview.length === 0 ? (
          <div className="uploadEmptyState">No deduplication found.</div>
        ) : (
          <>
            <div className="dedupStageCaseCount">
              Case {dedupCaseIndex + 1} of {dedupPreview.length}
            </div>

            {currentDedupCase && (
              <div className="dedupStageCard">
                <div className="dedupStageSummary">
                  Project "{currentDedupCase.projectName}" looks related to "{currentDedupCase.existingProjectName}".
                </div>

                <div className="dedupStageBadges">
                  <span className="dedupStageBadge">{currentDedupCase.similarityLabel}</span>
                  <span className="dedupStageBadge">{currentDedupCase.pathLabel}</span>
                  <span className="dedupStageBadge">{currentDedupCase.filesLabel}</span>
                </div>

                <label className="dedupStageOption">
                  <input
                    type="radio"
                    name={`dedup-${currentDedupCase.projectName}`}
                    value="new_project"
                    checked={dedupDecisions[currentDedupCase.projectName] === "new_project"}
                    onChange={() =>
                      setDedupDecisions((prev) => ({ ...prev, [currentDedupCase.projectName]: "new_project" }))
                    }
                  />
                  <span>New project (separate, no merge history created)</span>
                </label>

                <label className="dedupStageOption">
                  <input
                    type="radio"
                    name={`dedup-${currentDedupCase.projectName}`}
                    value="new_version"
                    checked={dedupDecisions[currentDedupCase.projectName] === "new_version"}
                    onChange={() =>
                      setDedupDecisions((prev) => ({ ...prev, [currentDedupCase.projectName]: "new_version" }))
                    }
                  />
                  <span>New version (links to existing history)</span>
                </label>
              </div>
            )}

            <div className="dedupStagePager">
              <button
                type="button"
                className="dedupStagePagerBtn"
                onClick={() => setDedupCaseIndex((prev) => prev - 1)}
                disabled={!canGoToPreviousDedupCase}
              >
                Previous case
              </button>
              <button
                type="button"
                className="dedupStagePagerBtn"
                onClick={() => setDedupCaseIndex((prev) => prev + 1)}
                disabled={!canGoToNextDedupCase}
              >
                Next case
              </button>
            </div>
          </>
        )}
      </div>
    );
  }

  function renderClassificationStage() {
    return (
      <div className="classificationStagePanel">
        <h2 className="wizardPlaceholderTitle">Classification and Type</h2>
        <p className="wizardPlaceholderText">Review each project and choose classification and project type one-by-one.</p>

        {projectsPreview.length === 0 ? (
          <div className="uploadEmptyState">No projects found.</div>
        ) : (
          <>
            <div className="classificationStageMeta">
              Project {classificationIndex + 1} of {projectsPreview.length}
              <span className="classificationStageMetaDivider">|</span>
              {completedClassificationCount} of {projectsPreview.length} completed
            </div>

            {currentClassificationProject && (
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
                    <tr>
                      <td>{currentClassificationProject}</td>
                      <td>
                        <select
                          className="classificationStageSelect"
                          value={classifications[currentClassificationProject] ?? ""}
                          onChange={(event) =>
                            setClassifications((prev) => ({
                              ...prev,
                              [currentClassificationProject]: event.target.value as ProjectClassificationValue,
                            }))
                          }
                        >
                          <option value="">Select</option>
                          <option value="individual">Individual</option>
                          <option value="collaborative">Collaborative</option>
                        </select>
                      </td>
                      <td>
                        <select
                          className="classificationStageSelect"
                          value={projectTypes[currentClassificationProject] ?? ""}
                          onChange={(event) =>
                            setProjectTypes((prev) => ({
                              ...prev,
                              [currentClassificationProject]: event.target.value as ProjectTypeValue,
                            }))
                          }
                        >
                          <option value="">Select</option>
                          <option value="text">Text</option>
                          <option value="code">Code</option>
                        </select>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}

            <div className="classificationStagePager">
              <button
                type="button"
                className="classificationStagePagerBtn"
                onClick={() => setClassificationIndex((prev) => prev - 1)}
                disabled={!canGoToPreviousClassificationProject}
              >
                Previous project
              </button>
              <button
                type="button"
                className="classificationStagePagerBtn"
                onClick={() => setClassificationIndex((prev) => prev + 1)}
                disabled={!canGoToNextClassificationProject}
              >
                Next project
              </button>
            </div>
          </>
        )}
      </div>
    );
  }

  function renderStageBody() {
    if (currentStage.key === "upload") return renderUploadStage();
    if (currentStage.key === "projects") return renderProjectsStage();
    if (currentStage.key === "deduplication") return renderDedupStage();
    return renderClassificationStage();
  }

  return (
    <UploadWizardShell
      username={username}
      steps={steps}
      actionLabel={actionLabel}
      onAction={onNext}
      actionDisabled={actionDisabled}
    >
      <div className="wizardPlaceholderCard">
        <div className="uploadStageTabs" role="tablist" aria-label="Upload flow stages">
          {STAGES.map((stage, idx) => {
            const active = idx === stageIndex;
            const disabled = idx > maxUnlockedStageIndex;

            return (
              <button
                key={stage.key}
                type="button"
                role="tab"
                aria-selected={active}
                disabled={disabled}
                className={`uploadStageTab${active ? " uploadStageTab--active" : ""}`}
                onClick={() => {
                  if (disabled) return;
                  setStageIndex(idx);
                }}
              >
                {idx + 1}. {stage.label}
              </button>
            );
          })}
        </div>

        {renderStageBody()}

        <div className="uploadStageNavRow">
          <button type="button" className="uploadStageBackBtn" onClick={onBack} disabled={!canGoBack}>
            Back
          </button>
        </div>
      </div>
    </UploadWizardShell>
  );
}
