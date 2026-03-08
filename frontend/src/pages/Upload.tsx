import { useMemo, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { getUsername } from "../auth/user";
import UploadWizardShell from "../components/UploadWizardShell";

type UploadFlowStage = "upload" | "projects" | "deduplication" | "classification";

type StageDef = {
  key: UploadFlowStage;
  label: string;
  title: string;
  description: string;
};

const STAGES: StageDef[] = [
  {
    key: "upload",
    label: "Upload",
    title: "Upload Placeholder",
    description: "Stage shell only: upload controls will be implemented next.",
  },
  {
    key: "projects",
    label: "Projects",
    title: "Projects Placeholder",
    description: "Projects list section will render here in the next step.",
  },
  {
    key: "deduplication",
    label: "Deduplication",
    title: "Deduplication Placeholder",
    description: "Deduplication cards will render here one-by-one in the next step.",
  },
  {
    key: "classification",
    label: "Classification",
    title: "Classification Placeholder",
    description: "Classification and type controls will render here in the next step.",
  },
];

export default function UploadPage() {
  const username = getUsername();
  const [stageIndex, setStageIndex] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const uploadInputRef = useRef<HTMLInputElement | null>(null);

  const currentStage = useMemo(() => STAGES[stageIndex], [stageIndex]);
  const canGoBack = stageIndex > 0;
  const canGoNext = stageIndex < STAGES.length - 1;
  const projectsPreview = useMemo(() => {
    if (!selectedFile) return [];
    return ["ProjectsA", "ProjectsB", "ProjectsC"];
  }, [selectedFile]);

  function onNext() {
    if (!canGoNext) return;
    setStageIndex((prev) => prev + 1);
  }

  function onBack() {
    if (!canGoBack) return;
    setStageIndex((prev) => prev - 1);
  }

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "active" as const },
    { label: "3. Setup", status: "disabled" as const, disabled: true },
  ];

  const sizeLabel = selectedFile ? `${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB` : null;

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

  function renderStageBody() {
    if (currentStage.key === "projects") {
      return (
        <div className="projectsStagePanel">
          <h2 className="wizardPlaceholderTitle">Projects</h2>
          <p className="wizardPlaceholderText">
            Parsed projects from the uploaded ZIP are shown here before deduplication.
          </p>

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

    if (currentStage.key !== "upload") {
      return (
        <>
          <h2 className="wizardPlaceholderTitle">{currentStage.title}</h2>
          <p className="wizardPlaceholderText">Current stage: {currentStage.label}</p>
          <div className="wizardPlaceholderNote">{currentStage.description}</div>
        </>
      );
    }

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

  return (
    <UploadWizardShell
      username={username}
      steps={steps}
      actionLabel="Next"
      onAction={onNext}
      actionDisabled={!canGoNext}
    >
      <div className="wizardPlaceholderCard">
        <div className="uploadStageTabs" role="tablist" aria-label="Upload flow stages">
          {STAGES.map((stage, idx) => {
            const active = idx === stageIndex;
            return (
              <button
                key={stage.key}
                type="button"
                role="tab"
                aria-selected={active}
                className={`uploadStageTab${active ? " uploadStageTab--active" : ""}`}
                onClick={() => setStageIndex(idx)}
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
