import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { getUsername } from "../../../auth/user";
import UploadWizardShell from "../../../components/UploadWizardShell";
import "../UploadShared.css";
import "./UploadPage.css";
import UploadStage from "./stages/UploadStage";
import ProjectsStage from "./stages/ProjectsStage";
import DedupStage from "./stages/DedupStage";
import ClassificationStage from "./stages/ClassificationStage";
import { STAGES } from "./uploadTypes";
import { useUploadFlow } from "./useUploadFlow";

export default function UploadPage() {
  const username = getUsername();
  const nav = useNavigate();
  const uploadInputRef = useRef<HTMLInputElement | null>(null);
  const flow = useUploadFlow();

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "active" as const },
    { label: "3. Setup", status: "disabled" as const, disabled: true },
    { label: "4. Analyze", status: "disabled" as const, disabled: true },
  ];

  function onSidebarNext() {
    if (flow.sidebarNextDisabled) return;
    if (!flow.uploadId) return;
    nav(`/upload/setup?uploadId=${flow.uploadId}`);
  }

  function renderStageBody() {
    if (flow.currentStage.key === "upload") {
      return (
        <UploadStage
          selectedFile={flow.selectedFile}
          sizeLabel={flow.sizeLabel}
          dragActive={flow.dragActive}
          uploadInputRef={uploadInputRef}
          onFileInputChange={flow.onFileInputChange}
          onDragOver={flow.onDragOver}
          onDragLeave={flow.onDragLeave}
          onDrop={flow.onDrop}
          onSelectFileClick={() => uploadInputRef.current?.click()}
        />
      );
    }

    if (flow.currentStage.key === "projects") {
      return (
        <ProjectsStage
          discoveredProjects={flow.discoveredProjects}
          projectNotes={flow.projectNotes}
          allProjectsPreviouslySkipped={flow.allProjectsPreviouslySkipped}
        />
      );
    }

    if (flow.currentStage.key === "deduplication") {
      return (
        <DedupStage
          visibleDedupCases={flow.visibleDedupCases}
          currentDedupCase={flow.currentDedupCase}
          dedupCaseIndex={flow.dedupCaseIndex}
          dedupDecisions={flow.dedupDecisions}
          savedDedupChoices={flow.savedDedupChoices}
          canGoToPreviousDedupCase={flow.canGoToPreviousDedupCase}
          canGoToNextDedupCase={flow.canGoToNextDedupCase}
          onDecisionChange={flow.onDedupDecisionChange}
          onPreviousCase={flow.onPreviousDedupCase}
          onNextCase={flow.onNextDedupCase}
        />
      );
    }

    return (
      <ClassificationStage
        classificationProjectsForDisplay={flow.classificationProjectsForDisplay}
        completedClassificationCount={flow.completedClassificationCount}
        classifications={flow.classifications}
        projectTypes={flow.projectTypes}
        autoAssignments={flow.autoAssignments}
        autoDetectedProjectTypes={flow.autoDetectedProjectTypes}
        existingClassifications={flow.existingClassifications}
        existingProjectTypes={flow.existingProjectTypes}
        onClassificationChange={flow.onClassificationChange}
        onProjectTypeChange={flow.onProjectTypeChange}
      />
    );
  }

  return (
    <UploadWizardShell
      username={username}
      steps={steps}
      actionLabel="Next"
      onAction={onSidebarNext}
      actionDisabled={flow.sidebarNextDisabled}
      showAction
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Upload", href: "/upload" },
        { label: "Upload", href: "/upload/upload" },
      ]}
    >
      <div className="wizardPlaceholderCard">
        <div className="uploadStageProgress" aria-label="Upload flow progress">
          <div className="uploadStageProgressMeta">
            <span>
              Step {flow.stageIndex + 1} of {STAGES.length}
            </span>
            <div className="uploadStageProgressStepNav" role="tablist" aria-label="Upload flow steps">
              {STAGES.map((stage, idx) => (
                <button
                  key={stage.key}
                  type="button"
                  role="tab"
                  aria-selected={idx === flow.stageIndex}
                  className={`uploadStageProgressStepBtn${
                    idx < flow.stageIndex ? " uploadStageProgressStepBtn--done" : ""
                  }${idx === flow.stageIndex ? " uploadStageProgressStepBtn--active" : ""}`}
                  disabled={flow.isSubmitting}
                  onClick={() => flow.onProgressStepClick(idx)}
                >
                  {idx + 1}. {stage.label}
                </button>
              ))}
            </div>
          </div>
          <div className="uploadStageProgressTrack">
            <div className="uploadStageProgressFill" style={{ width: `${flow.stageProgressPercent}%` }} />
          </div>
        </div>

        {flow.submitError && <p className="error uploadStatusLine">{flow.submitError}</p>}
        {renderStageBody()}

        <div className="uploadStageActionRow">
          <button
            type="button"
            className="uploadStageBackBtn"
            onClick={flow.onBack}
            disabled={!flow.canGoBack || flow.isSubmitting}
          >
            Back
          </button>

          <button
            type="button"
            className={`uploadStagePrimaryBtn${flow.classificationStageCompleted ? " uploadStagePrimaryBtn--completed" : ""}`}
            onClick={flow.onPrimaryAction}
            disabled={flow.primaryDisabled}
          >
            {flow.primaryLabel}
          </button>
        </div>
      </div>
    </UploadWizardShell>
  );
}
