import { useEffect, useMemo, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import {
  postProjectsUpload,
  postUploadClassifications,
  postUploadDedupResolve,
  postUploadProjectTypes,
} from "../../../api/uploads";
import type {
  DedupDecision,
  ProjectClassification,
  ProjectType,
  UploadRecord,
} from "../../../api/uploads";
import type {
  DedupCase,
  DedupDecisionValue,
  ProjectClassificationValue,
  ProjectTypeValue,
  VisibleDedupDecision,
} from "./uploadTypes";
import { STAGES } from "./uploadTypes";
import {
  asStringMap,
  getAutoAssignments,
  getAutoDetectedProjectTypes,
  getDedupCases,
  getDiscoveredProjects,
  getExistingClassifications,
  getExistingProjectTypes,
  getKnownProjects,
  getProjectNotes,
  getProjectsFromUpload,
  getProjectsNeedingType,
  isZipFile,
  SKIPPED_PROJECT_NOTE,
  toProjectClassificationValue,
  toProjectTypeValue,
  uploadState,
} from "./uploadHelpers";

export function useUploadFlow() {
  const [stageIndex, setStageIndex] = useState(0);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const [uploadData, setUploadData] = useState<UploadRecord | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [dedupCaseIndex, setDedupCaseIndex] = useState(0);
  const [dedupDecisions, setDedupDecisions] = useState<Record<string, DedupDecisionValue>>({});
  const [persistedDedupCases, setPersistedDedupCases] = useState<DedupCase[]>([]);

  const [classifications, setClassifications] = useState<Record<string, ProjectClassificationValue>>({});
  const [projectTypes, setProjectTypes] = useState<Record<string, ProjectTypeValue>>({});
  const [lastClassificationSubmitSignature, setLastClassificationSubmitSignature] = useState<string | null>(null);

  const currentStage = useMemo(() => STAGES[stageIndex], [stageIndex]);
  const canGoBack = stageIndex > 0;
  const stageProgressPercent = useMemo(() => {
    if (STAGES.length <= 1) return 100;
    return Math.round((stageIndex / (STAGES.length - 1)) * 100);
  }, [stageIndex]);

  const projects = useMemo(() => getProjectsFromUpload(uploadData), [uploadData]);
  const discoveredProjects = useMemo(() => getDiscoveredProjects(uploadData), [uploadData]);
  const knownProjects = useMemo(() => getKnownProjects(uploadData), [uploadData]);
  const projectsForFlow = useMemo(
    () => (projects.length > 0 ? projects : discoveredProjects),
    [projects, discoveredProjects],
  );
  const projectNotes = useMemo(() => getProjectNotes(uploadData), [uploadData]);
  const allProjectsPreviouslySkipped = useMemo(
    () =>
      discoveredProjects.length > 0 &&
      discoveredProjects.every((projectName) => projectNotes[projectName]?.includes(SKIPPED_PROJECT_NOTE)),
    [discoveredProjects, projectNotes],
  );

  const projectsNeedingType = useMemo(() => getProjectsNeedingType(uploadData), [uploadData]);
  const autoAssignments = useMemo(() => getAutoAssignments(uploadData), [uploadData]);
  const autoDetectedProjectTypes = useMemo(() => getAutoDetectedProjectTypes(uploadData), [uploadData]);
  const existingClassifications = useMemo(() => getExistingClassifications(uploadData), [uploadData]);
  const existingProjectTypes = useMemo(() => getExistingProjectTypes(uploadData), [uploadData]);

  const dedupCases = useMemo(() => getDedupCases(uploadData), [uploadData]);
  const visibleDedupCases = dedupCases.length > 0 ? dedupCases : persistedDedupCases;
  const currentDedupCase = visibleDedupCases[dedupCaseIndex] ?? null;
  const canGoToPreviousDedupCase = dedupCaseIndex > 0;
  const canGoToNextDedupCase = dedupCaseIndex < visibleDedupCases.length - 1;
  const savedDedupChoices = useMemo(
    () =>
      Object.entries(dedupDecisions).filter(
        (entry): entry is [string, VisibleDedupDecision] => entry[1] === "new_project" || entry[1] === "new_version",
      ),
    [dedupDecisions],
  );

  const needsClassification = uploadData?.status === "needs_classification";
  const needsProjectTypes = uploadData?.status === "needs_project_types";

  const newVersionSourceByTarget = useMemo(() => {
    const links: Record<string, string> = {};
    for (const entry of visibleDedupCases) {
      if (dedupDecisions[entry.projectName] !== "new_version") continue;
      const target = entry.existingProjectName.trim();
      if (!target || target === entry.projectName) continue;
      links[target] = entry.projectName;
    }
    return links;
  }, [dedupDecisions, visibleDedupCases]);

  const classificationProjectsForDisplay = useMemo(
    () => projectsForFlow.filter((projectName) => !newVersionSourceByTarget[projectName]),
    [newVersionSourceByTarget, projectsForFlow],
  );

  const classificationCompletionSignature = useMemo(() => {
    const rows = classificationProjectsForDisplay.map((projectName) => [
      projectName,
      toProjectClassificationValue(
        classifications[projectName] ?? autoAssignments[projectName] ?? existingClassifications[projectName],
      ),
      toProjectTypeValue(
        projectTypes[projectName] ?? autoDetectedProjectTypes[projectName] ?? existingProjectTypes[projectName],
      ),
    ]);
    const dedup = visibleDedupCases.map((entry) => [
      entry.projectName,
      entry.existingProjectName,
      dedupDecisions[entry.projectName] ?? "",
    ]);
    return JSON.stringify({ rows, dedup });
  }, [
    autoAssignments,
    autoDetectedProjectTypes,
    classificationProjectsForDisplay,
    classifications,
    dedupDecisions,
    existingClassifications,
    existingProjectTypes,
    projectTypes,
    visibleDedupCases,
  ]);

  const classificationDirtySinceSubmit = useMemo(
    () =>
      lastClassificationSubmitSignature !== null &&
      classificationCompletionSignature !== lastClassificationSubmitSignature,
    [classificationCompletionSignature, lastClassificationSubmitSignature],
  );

  const completedClassificationCount = useMemo(
    () =>
      classificationProjectsForDisplay.filter(
        (projectName) =>
          Boolean(
            toProjectClassificationValue(
              classifications[projectName] ?? autoAssignments[projectName] ?? existingClassifications[projectName],
            ),
          ) &&
          Boolean(
            toProjectTypeValue(
              projectTypes[projectName] ?? autoDetectedProjectTypes[projectName] ?? existingProjectTypes[projectName],
            ),
          ),
      ).length,
    [
      autoAssignments,
      autoDetectedProjectTypes,
      classificationProjectsForDisplay,
      classifications,
      existingClassifications,
      existingProjectTypes,
      projectTypes,
    ],
  );

  const dedupResolved = useMemo(
    () => visibleDedupCases.length === 0 || visibleDedupCases.every((entry) => Boolean(dedupDecisions[entry.projectName])),
    [dedupDecisions, visibleDedupCases],
  );

  const allClassificationRowsComplete = useMemo(
    () =>
      classificationProjectsForDisplay.length > 0 &&
      classificationProjectsForDisplay.every(
        (projectName) =>
          Boolean(
            toProjectClassificationValue(
              classifications[projectName] ?? autoAssignments[projectName] ?? existingClassifications[projectName],
            ),
          ) &&
          Boolean(
            toProjectTypeValue(
              projectTypes[projectName] ?? autoDetectedProjectTypes[projectName] ?? existingProjectTypes[projectName],
            ),
          ),
      ),
    [
      autoAssignments,
      autoDetectedProjectTypes,
      classificationProjectsForDisplay,
      classifications,
      existingClassifications,
      existingProjectTypes,
      projectTypes,
    ],
  );

  const classificationReady = useMemo(() => {
    if (!uploadData) return false;
    let hasRequirement = false;

    if (needsClassification) {
      hasRequirement = true;
      if (knownProjects.length === 0) return false;
      for (const projectName of knownProjects) {
        const linkedSource = newVersionSourceByTarget[projectName];
        const value =
          toProjectClassificationValue(
            classifications[projectName] ?? autoAssignments[projectName] ?? existingClassifications[projectName],
          ) ||
          (linkedSource
            ? toProjectClassificationValue(
                classifications[linkedSource] ??
                  autoAssignments[linkedSource] ??
                  existingClassifications[linkedSource],
              )
            : "");
        if (!value) return false;
      }
    }

    if (needsProjectTypes) {
      hasRequirement = true;
      if (projectsNeedingType.length === 0) return false;
      for (const projectName of projectsNeedingType) {
        const linkedSource = newVersionSourceByTarget[projectName];
        const value =
          toProjectTypeValue(
            projectTypes[projectName] ?? autoDetectedProjectTypes[projectName] ?? existingProjectTypes[projectName],
          ) ||
          (linkedSource
            ? toProjectTypeValue(
                projectTypes[linkedSource] ??
                  autoDetectedProjectTypes[linkedSource] ??
                  existingProjectTypes[linkedSource],
              )
            : "");
        if (!value) return false;
      }
    }

    return hasRequirement;
  }, [
    classifications,
    knownProjects,
    needsClassification,
    needsProjectTypes,
    newVersionSourceByTarget,
    autoAssignments,
    autoDetectedProjectTypes,
    existingClassifications,
    existingProjectTypes,
    projectTypes,
    projectsNeedingType,
    uploadData,
  ]);

  const classificationStageCompleted =
    Boolean(uploadData) &&
    !needsClassification &&
    !needsProjectTypes &&
    allClassificationRowsComplete &&
    !classificationDirtySinceSubmit;

  const primaryLabel = useMemo(() => {
    if (isSubmitting) {
      if (currentStage.key === "upload") return "Uploading...";
      return "Saving...";
    }

    if (currentStage.key === "classification") {
      if (classificationStageCompleted) return "Continue to Setup";
      if (uploadData && !needsClassification && !needsProjectTypes && classificationDirtySinceSubmit) return "Resubmit";
      return "Submit and Continue";
    }

    if (currentStage.key === "deduplication") return "Resolve and Continue";
    return "Next";
  }, [
    classificationDirtySinceSubmit,
    classificationStageCompleted,
    currentStage.key,
    isSubmitting,
    needsClassification,
    needsProjectTypes,
    uploadData,
  ]);

  const primaryDisabled = useMemo(() => {
    if (isSubmitting) return true;

    if (currentStage.key === "upload") return !selectedFile;
    if (currentStage.key === "projects") {
      return !uploadData || discoveredProjects.length === 0 || allProjectsPreviouslySkipped;
    }
    if (currentStage.key === "deduplication") return !uploadData || !dedupResolved;

    if (!uploadData) return true;
    if (currentStage.key === "classification" && classificationStageCompleted) {
      return !uploadData.upload_id;
    }
    if (!allClassificationRowsComplete) return true;
    if (!needsClassification && !needsProjectTypes) return !classificationDirtySinceSubmit;
    return !classificationReady;
  }, [
    allClassificationRowsComplete,
    classificationDirtySinceSubmit,
    classificationReady,
    classificationStageCompleted,
    currentStage.key,
    dedupResolved,
    allProjectsPreviouslySkipped,
    discoveredProjects.length,
    isSubmitting,
    needsClassification,
    needsProjectTypes,
    selectedFile,
    uploadData,
  ]);

  const sizeLabel = selectedFile ? `${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB` : null;

  useEffect(() => {
    if (dedupCases.length > 0) {
      setPersistedDedupCases(dedupCases);
    }
  }, [dedupCases]);

  useEffect(() => {
    if (!uploadData) {
      setLastClassificationSubmitSignature(null);
      return;
    }
    if (lastClassificationSubmitSignature !== null) return;
    if (!needsClassification && !needsProjectTypes && allClassificationRowsComplete) {
      setLastClassificationSubmitSignature(classificationCompletionSignature);
    }
  }, [
    allClassificationRowsComplete,
    classificationCompletionSignature,
    lastClassificationSubmitSignature,
    needsClassification,
    needsProjectTypes,
    uploadData,
  ]);

  useEffect(() => {
    setDedupCaseIndex(0);
    const existingDecisions = asStringMap(uploadState(uploadData).dedup_resolved);
    setDedupDecisions((prev) => {
      const next: Record<string, DedupDecisionValue> = {};
      for (const [projectName, value] of Object.entries(prev)) {
        if (value === "new_project" || value === "new_version") {
          next[projectName] = value;
        }
      }
      for (const [projectName, value] of Object.entries(existingDecisions)) {
        if (value === "new_project" || value === "new_version") {
          next[projectName] = value;
        }
      }
      return next;
    });

    const seededClassifications = {
      ...autoAssignments,
      ...existingClassifications,
    };
    setClassifications((prev) => {
      const next = { ...prev };
      for (const [projectName, value] of Object.entries(seededClassifications)) {
        if (value === "individual" || value === "collaborative") {
          next[projectName] = value;
        }
      }
      return next;
    });

    const seededTypes = existingProjectTypes;
    setProjectTypes((prev) => {
      const next = { ...prev };
      for (const [projectName, value] of Object.entries(seededTypes)) {
        if (value === "code" || value === "text") {
          next[projectName] = value;
        }
      }
      return next;
    });
  }, [autoAssignments, existingClassifications, existingProjectTypes, uploadData]);

  useEffect(() => {
    if (dedupCaseIndex <= visibleDedupCases.length - 1) return;
    setDedupCaseIndex(0);
  }, [dedupCaseIndex, visibleDedupCases.length]);

  function resetFlowForNewFile(file: File | null) {
    setSelectedFile(file);
    setUploadData(null);
    setSubmitError(null);
    setLastClassificationSubmitSignature(null);
    setDedupCaseIndex(0);
    setDedupDecisions({});
    setPersistedDedupCases([]);
    setClassifications({});
    setProjectTypes({});
    setStageIndex(0);
  }

  function onBack() {
    if (!canGoBack || isSubmitting) return;
    setStageIndex((prev) => prev - 1);
  }

  async function runCurrentStageAction(stageKey: (typeof STAGES)[number]["key"]): Promise<boolean> {
    if (stageKey === "upload") return handleUploadNext();
    if (stageKey === "projects") return handleProjectsNext();
    if (stageKey === "deduplication") return handleDedupNext();
    return handleClassificationNext();
  }

  async function onProgressStepClick(targetIndex: number) {
    if (isSubmitting) return;

    if (targetIndex <= stageIndex) {
      setStageIndex(targetIndex);
      return;
    }

    if (targetIndex !== stageIndex + 1) return;

    const stageKey = STAGES[stageIndex]?.key;
    if (!stageKey) return;
    await runCurrentStageAction(stageKey);
  }

  function selectZipFile(file: File | null) {
    if (!file) {
      resetFlowForNewFile(null);
      return;
    }

    if (!isZipFile(file)) {
      resetFlowForNewFile(null);
      setSubmitError("Only ZIP files are allowed.");
      return;
    }

    resetFlowForNewFile(file);
  }

  function onFileInputChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    selectZipFile(file);
    if (file && !isZipFile(file)) {
      event.target.value = "";
    }
  }

  function onDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(true);
  }

  function onDragLeave() {
    setDragActive(false);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0] ?? null;
    selectZipFile(file);
  }

  async function handleUploadNext(): Promise<boolean> {
    if (!selectedFile) return false;

    if (!isZipFile(selectedFile)) {
      setSubmitError("Only ZIP files are allowed.");
      return false;
    }

    setSubmitError(null);
    setIsSubmitting(true);

    try {
      const response = await postProjectsUpload(selectedFile, selectedFile.name);
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "Upload failed.");
      }

      setUploadData(response.data);
      setStageIndex(STAGES.findIndex((stage) => stage.key === "projects"));
      return true;
    } catch (e: unknown) {
      setSubmitError(e instanceof Error ? e.message : "Upload failed.");
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleProjectsNext(): boolean {
    if (!uploadData) return false;

    if (discoveredProjects.length === 0) {
      setSubmitError("No projects found. Upload another ZIP file to continue.");
      return false;
    }
    if (allProjectsPreviouslySkipped) {
      setSubmitError("No projects to analyze in this upload because all detected projects were previously skipped.");
      return false;
    }

    setSubmitError(null);
    setStageIndex(STAGES.findIndex((stage) => stage.key === "deduplication"));
    return true;
  }

  async function handleDedupNext(): Promise<boolean> {
    if (!uploadData) return false;

    setSubmitError(null);

    if (visibleDedupCases.length === 0) {
      setStageIndex(STAGES.findIndex((stage) => stage.key === "classification"));
      return true;
    }

    const decisions: Record<string, DedupDecision> = {};
    for (const entry of visibleDedupCases) {
      const selected = dedupDecisions[entry.projectName];
      if (!selected) {
        setSubmitError(`Please choose a decision for ${entry.projectName}.`);
        return false;
      }
      decisions[entry.projectName] = selected;
    }

    if (uploadData.status !== "needs_dedup") {
      setStageIndex(STAGES.findIndex((stage) => stage.key === "classification"));
      return true;
    }

    setIsSubmitting(true);
    try {
      const response = await postUploadDedupResolve(uploadData.upload_id, decisions);
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "Failed to save deduplication decisions.");
      }
      setUploadData(response.data);
      setStageIndex(STAGES.findIndex((stage) => stage.key === "classification"));
      return true;
    } catch (e: unknown) {
      setSubmitError(e instanceof Error ? e.message : "Failed to save deduplication decisions.");
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleClassificationNext(): Promise<boolean> {
    if (!uploadData) return false;

    setSubmitError(null);

    const shouldResubmitCompleted = !needsClassification && !needsProjectTypes && classificationDirtySinceSubmit;
    if (!needsClassification && !needsProjectTypes && !shouldResubmitCompleted) {
      return true;
    }

    let workingUpload = uploadData;
    setIsSubmitting(true);

    try {
      const shouldSubmitClassifications = workingUpload.status === "needs_classification" || shouldResubmitCompleted;
      if (shouldSubmitClassifications) {
        const targets = getKnownProjects(workingUpload);
        const assignments: Record<string, ProjectClassification> = {};

        if (targets.length === 0) {
          throw new Error("No projects available for classification.");
        }

        const existingAssignments = getExistingClassifications(workingUpload);
        for (const projectName of targets) {
          const linkedSource = newVersionSourceByTarget[projectName];
          const value =
            toProjectClassificationValue(
              classifications[projectName] ?? autoAssignments[projectName] ?? existingAssignments[projectName],
            ) ||
            (linkedSource
              ? toProjectClassificationValue(
                  classifications[linkedSource] ?? autoAssignments[linkedSource] ?? existingAssignments[linkedSource],
                )
              : "");
          if (value !== "individual" && value !== "collaborative") {
            throw new Error(`Please choose a classification for ${projectName}.`);
          }
          assignments[projectName] = value;
        }

        const response = await postUploadClassifications(workingUpload.upload_id, assignments);
        if (!response.success || !response.data) {
          throw new Error(response.error?.message ?? "Failed to save classifications.");
        }
        workingUpload = response.data;
      }

      const shouldSubmitProjectTypes = workingUpload.status === "needs_project_types" || shouldResubmitCompleted;
      if (shouldSubmitProjectTypes) {
        const requiredProjectsNeedingType = getProjectsNeedingType(workingUpload);
        const typeTargets = shouldResubmitCompleted ? getKnownProjects(workingUpload) : requiredProjectsNeedingType;
        const project_types: Record<string, ProjectType> = {};
        const existingTypes = getExistingProjectTypes(workingUpload);

        for (const projectName of typeTargets) {
          const linkedSource = newVersionSourceByTarget[projectName];
          const value =
            toProjectTypeValue(
              projectTypes[projectName] ?? autoDetectedProjectTypes[projectName] ?? existingTypes[projectName],
            ) ||
            (linkedSource
              ? toProjectTypeValue(
                  projectTypes[linkedSource] ?? autoDetectedProjectTypes[linkedSource] ?? existingTypes[linkedSource],
                )
              : "");
          if (value !== "code" && value !== "text") {
            throw new Error(`Please choose a project type for ${projectName}.`);
          }
          project_types[projectName] = value;
        }

        for (const projectName of requiredProjectsNeedingType) {
          if (!project_types[projectName]) {
            throw new Error(`Please choose a project type for ${projectName}.`);
          }
        }

        const response = await postUploadProjectTypes(workingUpload.upload_id, project_types);
        if (!response.success || !response.data) {
          throw new Error(response.error?.message ?? "Failed to save project types.");
        }
        workingUpload = response.data;
      }

      setUploadData(workingUpload);
      setLastClassificationSubmitSignature(classificationCompletionSignature);
      return true;
    } catch (e: unknown) {
      setSubmitError(e instanceof Error ? e.message : "Failed to save classification data.");
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onPrimaryAction(): Promise<boolean> {
    if (primaryDisabled) return false;
    return runCurrentStageAction(currentStage.key);
  }

  function onDedupDecisionChange(projectName: string, value: VisibleDedupDecision) {
    setDedupDecisions((prev) => ({ ...prev, [projectName]: value }));
  }

  function onPreviousDedupCase() {
    setDedupCaseIndex((prev) => prev - 1);
  }

  function onNextDedupCase() {
    setDedupCaseIndex((prev) => prev + 1);
  }

  function onClassificationChange(projectName: string, value: ProjectClassificationValue) {
    setClassifications((prev) => ({
      ...prev,
      [projectName]: value,
    }));
  }

  function onProjectTypeChange(projectName: string, value: ProjectTypeValue) {
    setProjectTypes((prev) => ({
      ...prev,
      [projectName]: value,
    }));
  }

  return {
    uploadId: uploadData?.upload_id ?? null,
    stageIndex,
    currentStage,
    canGoBack,
    stageProgressPercent,
    selectedFile,
    sizeLabel,
    dragActive,
    submitError,
    isSubmitting,
    primaryLabel,
    primaryDisabled,
    classificationStageCompleted,
    discoveredProjects,
    projectNotes,
    allProjectsPreviouslySkipped,
    visibleDedupCases,
    currentDedupCase,
    dedupCaseIndex,
    dedupDecisions,
    savedDedupChoices,
    canGoToPreviousDedupCase,
    canGoToNextDedupCase,
    classificationProjectsForDisplay,
    completedClassificationCount,
    classifications,
    projectTypes,
    autoAssignments,
    autoDetectedProjectTypes,
    existingClassifications,
    existingProjectTypes,
    onBack,
    onProgressStepClick,
    onPrimaryAction,
    onFileInputChange,
    onDragOver,
    onDragLeave,
    onDrop,
    onDedupDecisionChange,
    onPreviousDedupCase,
    onNextDedupCase,
    onClassificationChange,
    onProjectTypeChange,
  };
}
