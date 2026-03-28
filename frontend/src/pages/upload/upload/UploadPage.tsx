import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { deleteUpload, getUploads, type UploadListItem, type UploadStatus } from "../../../api/uploads";
import { getUsername } from "../../../auth/user";
import UploadWizardShell from "../../../components/UploadWizardShell";
import "../UploadShared.css";
import "./UploadPage.css";
import UploadConfirmDialog from "./components/UploadConfirmDialog";
import UploadStage from "./stages/UploadStage";
import ProjectsStage from "./stages/ProjectsStage";
import DedupStage from "./stages/DedupStage";
import ClassificationStage from "./stages/ClassificationStage";
import {
  clearUploadRecoveryStage,
  readUploadRecoveryStage,
  recoveryRouteForUpload,
  saveUploadRecoveryStage,
} from "./recoveryStage";
import { STAGES } from "./uploadTypes";
import { useUploadFlow } from "./useUploadFlow";
import { useUnfinishedUploadExitGuard } from "../hooks/useUnfinishedUploadExitGuard";

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

export default function UploadPage() {
  const username = getUsername();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const uploadInputRef = useRef<HTMLInputElement | null>(null);
  const uploadIdParam = searchParams.get("uploadId");
  const stageParam = searchParams.get("stage");
  const flow = useUploadFlow(uploadIdParam, stageParam);
  const pendingLeaveNavigationRef = useRef<(() => Promise<void>) | null>(null);
  const [checkedRecovery, setCheckedRecovery] = useState(false);
  const [recoveryCandidate, setRecoveryCandidate] = useState<UploadListItem | null>(null);
  const [recoveryError, setRecoveryError] = useState<string | null>(null);
  const [isResolvingRecovery, setIsResolvingRecovery] = useState(false);
  const [continueAfterStartFresh, setContinueAfterStartFresh] = useState(false);
  const [replaceUnfinishedDialogOpen, setReplaceUnfinishedDialogOpen] = useState(false);
  const [leaveUploadDialogOpen, setLeaveUploadDialogOpen] = useState(false);

  useUnfinishedUploadExitGuard({
    enabled: Boolean(flow.uploadId),
    uploadId: flow.uploadId,
    message: "Leave upload flow? Your unfinished upload will be deleted.",
    onRequestConfirmLeave: (confirmNavigation) => {
      pendingLeaveNavigationRef.current = confirmNavigation;
      setLeaveUploadDialogOpen(true);
    },
    onCleanupError: (message) => {
      setRecoveryError(message);
    },
  });

  useEffect(() => {
    if (!flow.uploadId) return;
    saveUploadRecoveryStage(flow.uploadId, flow.currentStage.key);
  }, [flow.currentStage.key, flow.uploadId]);

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

  async function runPrimaryAction() {
    const succeeded = await flow.onPrimaryAction();
    if (!succeeded) return;

    if (flow.currentStage.key === "classification" && flow.uploadId) {
      nav(`/upload/setup?uploadId=${flow.uploadId}`);
    }
  }

  async function onPrimaryClick() {
    const requiresReplaceConfirmation =
      flow.currentStage.key === "upload" &&
      !flow.uploadId &&
      Boolean(recoveryCandidate);
    if (requiresReplaceConfirmation) {
      setContinueAfterStartFresh(true);
      setReplaceUnfinishedDialogOpen(true);
      return;
    }
    await runPrimaryAction();
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
        if (active) setCheckedRecovery(true);
      }
    }

    void loadRecoveryCandidate();
    return () => {
      active = false;
    };
  }, [checkedRecovery, uploadIdParam]);

  useEffect(() => {
    if (!checkedRecovery) return;
    if (uploadIdParam) return;
    if (flow.currentStage.key !== "upload") return;
    if (flow.selectedFile) return;
    if (!recoveryCandidate) return;
    setReplaceUnfinishedDialogOpen(true);
  }, [checkedRecovery, flow.currentStage.key, flow.selectedFile, recoveryCandidate, uploadIdParam]);

  async function onStartFreshFromRecoveryDialog() {
    if (!recoveryCandidate) return;
    setRecoveryError(null);
    setIsResolvingRecovery(true);
    try {
      const res = await deleteUpload(recoveryCandidate.upload_id);
      if (!res.success) {
        throw new Error(res.error?.message ?? "Failed to remove previous unfinished upload.");
      }
      clearUploadRecoveryStage(recoveryCandidate.upload_id);
      setRecoveryCandidate(null);
      setReplaceUnfinishedDialogOpen(false);
      if (continueAfterStartFresh) {
        await runPrimaryAction();
      }
    } catch (error: unknown) {
      setRecoveryError(error instanceof Error ? error.message : "Failed to remove previous unfinished upload.");
    } finally {
      setContinueAfterStartFresh(false);
      setIsResolvingRecovery(false);
    }
  }

  function onResumeRecoveryUpload() {
    if (!recoveryCandidate) return;
    setReplaceUnfinishedDialogOpen(false);
    setContinueAfterStartFresh(false);
    const rememberedStage = readUploadRecoveryStage(recoveryCandidate.upload_id);
    nav(recoveryRouteForUpload(recoveryCandidate, rememberedStage));
  }

  function onCancelLeaveUploadFlow() {
    pendingLeaveNavigationRef.current = null;
    setLeaveUploadDialogOpen(false);
  }

  function onConfirmLeaveUploadFlow() {
    const confirmNavigation = pendingLeaveNavigationRef.current;
    pendingLeaveNavigationRef.current = null;
    setLeaveUploadDialogOpen(false);
    if (confirmNavigation) void confirmNavigation();
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
        {recoveryError && <p className="error uploadStatusLine">{recoveryError}</p>}
        {renderStageBody()}

        <div className="uploadStageActionRow">
          <button
            type="button"
            className="uploadStageBackBtn"
            onClick={flow.onBack}
            disabled={!flow.canGoBack || flow.isSubmitting || isResolvingRecovery}
          >
            Back
          </button>

          <button
            type="button"
            className={`uploadStagePrimaryBtn${flow.classificationStageCompleted ? " uploadStagePrimaryBtn--completed" : ""}`}
            onClick={onPrimaryClick}
            disabled={flow.primaryDisabled || isResolvingRecovery}
          >
            {flow.primaryLabel}
          </button>
        </div>
      </div>
      <UploadConfirmDialog
        open={leaveUploadDialogOpen}
        title="Leave Upload Flow?"
        description="Your unfinished upload will be deleted if you leave now."
        confirmLabel="Leave"
        onCancel={onCancelLeaveUploadFlow}
        onConfirm={onConfirmLeaveUploadFlow}
      />
      <UploadConfirmDialog
        open={replaceUnfinishedDialogOpen}
        title="Unfinished Upload Found"
        description={
          recoveryCandidate?.zip_name
            ? `You still have an unfinished upload (${recoveryCandidate.zip_name}). Resume where you left off, or start a new upload.`
            : "You still have an unfinished upload. Resume where you left off, or start a new upload."
        }
        cancelLabel={isResolvingRecovery ? "Deleting..." : "Start New"}
        confirmLabel="Resume"
        confirmDisabled={isResolvingRecovery}
        onCancel={() => {
          if (isResolvingRecovery) return;
          void onStartFreshFromRecoveryDialog();
        }}
        onConfirm={() => {
          if (isResolvingRecovery) return;
          onResumeRecoveryUpload();
        }}
      />
    </UploadWizardShell>
  );
}
