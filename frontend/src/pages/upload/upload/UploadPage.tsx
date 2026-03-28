import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { deleteUpload, getUploads, type UploadListItem, type UploadStatus } from "../../../api/uploads";
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

const RECOVERABLE_UPLOAD_STATUSES = new Set<UploadStatus>([
  "started",
  "parsed",
  "needs_dedup",
  "needs_classification",
  "needs_project_types",
  "needs_file_roles",
  "needs_summaries",
  "failed",
]);

function recoveryRouteForUpload(upload: UploadListItem): string {
  if (upload.status === "needs_file_roles" || upload.status === "needs_summaries") {
    return `/upload/setup?uploadId=${upload.upload_id}`;
  }
  return `/upload/upload?uploadId=${upload.upload_id}&stage=classification`;
}

export default function UploadPage() {
  const username = getUsername();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const uploadInputRef = useRef<HTMLInputElement | null>(null);
  const uploadIdParam = searchParams.get("uploadId");
  const stageParam = searchParams.get("stage");
  const classificationResumeUploadId = stageParam === "classification" ? uploadIdParam : null;
  const flow = useUploadFlow(classificationResumeUploadId);
  const [isCancelling, setIsCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);
  const [checkedRecovery, setCheckedRecovery] = useState(false);
  const [recoveryCandidate, setRecoveryCandidate] = useState<UploadListItem | null>(null);
  const [recoveryError, setRecoveryError] = useState<string | null>(null);
  const [isResolvingRecovery, setIsResolvingRecovery] = useState(false);

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "active" as const },
    { label: "3. Setup", status: "disabled" as const, disabled: true },
    { label: "4. Analyze", status: "disabled" as const, disabled: true },
  ];

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
          onOpenProjectDetailsInNewTab={flow.onOpenProjectDetailsInNewTab}
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

  async function onPrimaryClick() {
    const succeeded = await flow.onPrimaryAction();
    if (!succeeded) return;

    if (flow.currentStage.key === "classification" && flow.uploadId) {
      nav(`/upload/setup?uploadId=${flow.uploadId}`);
    }
  }

  useEffect(() => {
    if (checkedRecovery) return;
    if (uploadIdParam) {
      setCheckedRecovery(true);
      return;
    }

    let active = true;
    async function loadRecoveryCandidate() {
      try {
        const res = await getUploads(10, 0);
        const uploads = res.data?.uploads ?? [];
        if (!active) return;
        const latestUnfinished = uploads.find((item) => RECOVERABLE_UPLOAD_STATUSES.has(item.status)) ?? null;
        setRecoveryCandidate(latestUnfinished);
      } catch (error: unknown) {
        if (!active) return;
        setRecoveryError(error instanceof Error ? error.message : "Failed to check unfinished uploads.");
      } finally {
        if (!active) return;
        setCheckedRecovery(true);
      }
    }

    void loadRecoveryCandidate();
    return () => {
      active = false;
    };
  }, [checkedRecovery, uploadIdParam]);

  function onContinueRecovery() {
    if (!recoveryCandidate) return;
    nav(recoveryRouteForUpload(recoveryCandidate));
  }

  async function onStartFreshRecovery() {
    if (!recoveryCandidate || isResolvingRecovery) return;
    const confirmed = window.confirm(
      "Start fresh? The previous unfinished upload will be deleted.",
    );
    if (!confirmed) return;

    setRecoveryError(null);
    setIsResolvingRecovery(true);
    try {
      const res = await deleteUpload(recoveryCandidate.upload_id);
      if (!res.success) {
        throw new Error(res.error?.message ?? "Failed to remove previous unfinished upload.");
      }
      setRecoveryCandidate(null);
    } catch (error: unknown) {
      setRecoveryError(error instanceof Error ? error.message : "Failed to remove previous unfinished upload.");
    } finally {
      setIsResolvingRecovery(false);
    }
  }

  async function onExitUploadWizard() {
    if (isCancelling) return;
    const confirmed = window.confirm(
      "Exit upload flow? Your unfinished upload will be deleted.",
    );
    if (!confirmed) return;

    setCancelError(null);
    setIsCancelling(true);
    try {
      if (flow.uploadId) {
        const res = await deleteUpload(flow.uploadId);
        if (!res.success) {
          throw new Error(res.error?.message ?? "Failed to cancel upload.");
        }
      }
      nav("/projects");
    } catch (error: unknown) {
      setCancelError(error instanceof Error ? error.message : "Failed to cancel upload.");
    } finally {
      setIsCancelling(false);
    }
  }

  return (
    <UploadWizardShell
      username={username}
      steps={steps}
      actionLabel="Next"
      showAction={false}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Upload", href: "/upload" },
        { label: "Upload", href: "/upload/upload" },
      ]}
    >
      <div className="wizardPlaceholderCard">
        {!flow.uploadId && !flow.selectedFile && recoveryCandidate && (
          <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-3">
            <p className="text-sm font-semibold text-amber-800">Unfinished upload detected</p>
            <p className="mt-1 text-sm text-amber-900">
              {recoveryCandidate.zip_name
                ? `You still have an unfinished upload (${recoveryCandidate.zip_name}).`
                : "You still have an unfinished upload."}{" "}
              Continue it or start fresh.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded-md border border-amber-300 bg-white px-3 py-1.5 text-sm font-semibold text-amber-900"
                onClick={onContinueRecovery}
                disabled={isResolvingRecovery}
              >
                Continue previous
              </button>
              <button
                type="button"
                className="rounded-md border border-rose-300 bg-rose-50 px-3 py-1.5 text-sm font-semibold text-rose-700"
                onClick={onStartFreshRecovery}
                disabled={isResolvingRecovery}
              >
                {isResolvingRecovery ? "Deleting..." : "Start fresh"}
              </button>
              <button
                type="button"
                className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm font-semibold text-zinc-700"
                onClick={() => setRecoveryCandidate(null)}
                disabled={isResolvingRecovery}
              >
                Dismiss
              </button>
            </div>
          </div>
        )}
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
        {cancelError && <p className="error uploadStatusLine">{cancelError}</p>}
        {recoveryError && <p className="error uploadStatusLine">{recoveryError}</p>}
        {renderStageBody()}

        <div className="uploadStageActionRow">
          <div className="uploadStageActionRowLeft">
            <button
              type="button"
              className="uploadStageExitBtn"
              onClick={onExitUploadWizard}
              disabled={isCancelling || flow.isSubmitting}
            >
              {isCancelling ? "Exiting..." : "Exit"}
            </button>
            <button
              type="button"
              className="uploadStageBackBtn"
              onClick={flow.onBack}
              disabled={!flow.canGoBack || flow.isSubmitting || isCancelling}
            >
              Back
            </button>
          </div>

          <button
            type="button"
            className={`uploadStagePrimaryBtn${flow.classificationStageCompleted ? " uploadStagePrimaryBtn--completed" : ""}`}
            onClick={onPrimaryClick}
            disabled={flow.primaryDisabled || isCancelling}
          >
            {flow.primaryLabel}
          </button>
        </div>
      </div>
    </UploadWizardShell>
  );
}
