import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import { getUsername } from "../auth/user";
import UploadWizardShell from "../components/UploadWizardShell";
import "./Upload.css";
import {
  postProjectsUpload,
  postUploadClassifications,
  postUploadDedupResolve,
  postUploadProjectTypes,
} from "../api/uploads";
import type {
  DedupDecision,
  ProjectClassification,
  ProjectType,
  UploadRecord,
} from "../api/uploads";

type UploadFlowStage = "upload" | "projects" | "deduplication" | "classification";

type StageDef = {
  key: UploadFlowStage;
  label: string;
};

type DedupDecisionValue = "" | DedupDecision;
type ProjectClassificationValue = "" | ProjectClassification;
type ProjectTypeValue = "" | ProjectType;

type DedupCase = {
  projectName: string;
  existingProjectName: string;
  similarityLabel?: string;
  pathLabel?: string;
  filesLabel?: string;
};

const STAGES: StageDef[] = [
  { key: "upload", label: "Upload" },
  { key: "projects", label: "Projects" },
  { key: "deduplication", label: "Deduplication" },
  { key: "classification", label: "Classification" },
];

function asRecord(value: unknown): Record<string, unknown> {
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return parsed as Record<string, unknown>;
      }
    } catch {
      return {};
    }
    return {};
  }

  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return value as Record<string, unknown>;
}

function asStringArray(value: unknown): string[] {
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) {
        return parsed.filter((entry): entry is string => typeof entry === "string" && entry.trim().length > 0);
      }
    } catch {
      return [];
    }
  }

  if (!Array.isArray(value)) return [];
  return value.filter((entry): entry is string => typeof entry === "string" && entry.trim().length > 0);
}

function asStringMap(value: unknown): Record<string, string> {
  const out: Record<string, string> = {};
  const obj = asRecord(value);
  for (const [k, v] of Object.entries(obj)) {
    if (typeof v === "string" && v.trim().length > 0) out[k] = v;
  }
  return out;
}

function objectKeys(value: unknown): string[] {
  return Object.keys(asRecord(value)).filter((key) => key.trim().length > 0);
}

function uniqueStrings(items: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const item of items) {
    if (seen.has(item)) continue;
    seen.add(item);
    out.push(item);
  }
  return out;
}

function uploadState(upload: UploadRecord | null): Record<string, unknown> {
  return asRecord(upload?.state);
}

function layoutState(upload: UploadRecord | null): Record<string, unknown> {
  return asRecord(uploadState(upload).layout);
}

function getProjectsFromUpload(upload: UploadRecord | null): string[] {
  const layout = layoutState(upload);
  const pending = asStringArray(layout.pending_projects);
  const layoutProjects = asStringArray(layout.projects);
  const auto = Object.keys(asStringMap(layout.auto_assignments));
  const state = uploadState(upload);
  const keyed = objectKeys(state.dedup_project_keys);
  const versionKeyed = objectKeys(state.dedup_version_keys);
  const asks = objectKeys(state.dedup_asks);
  const resolved = objectKeys(state.dedup_resolved);
  const classified = objectKeys(state.classifications);
  const typeAuto = objectKeys(state.project_types_auto);
  const typeManual = objectKeys(state.project_types_manual);
  const filetypeIndex = objectKeys(state.project_filetype_index);

  return uniqueStrings([
    ...pending,
    ...layoutProjects,
    ...auto,
    ...keyed,
    ...versionKeyed,
    ...asks,
    ...resolved,
    ...classified,
    ...typeAuto,
    ...typeManual,
    ...filetypeIndex,
  ]);
}

function getDiscoveredProjects(upload: UploadRecord | null): string[] {
  const state = uploadState(upload);
  const layout = layoutState(upload);
  const zipName = typeof upload?.zip_name === "string" ? upload.zip_name.trim() : "";
  const zipStem = zipName.toLowerCase().endsWith(".zip") ? zipName.slice(0, -4) : zipName;

  const dedupSkipped = asStringArray(state.dedup_skipped_projects);
  const dedupNewVersions = asStringMap(state.dedup_new_versions);
  const dedupRenamedFrom = Object.keys(dedupNewVersions);
  const dedupRenamedTo = uniqueStrings(Object.values(dedupNewVersions).filter((name) => name.trim().length > 0));

  const strayLocations = asStringArray(layout.stray_locations);

  const discovered = uniqueStrings([
    ...getProjectsFromUpload(upload),
    ...dedupSkipped,
    ...dedupRenamedFrom,
    ...dedupRenamedTo,
    ...strayLocations,
  ]);

  return discovered.filter((name) => {
    const normalized = name.trim().toLowerCase();
    if (!normalized) return false;
    if (normalized.endsWith(".zip")) return false;
    if (zipName && normalized === zipName.toLowerCase()) return false;
    if (zipStem && normalized === zipStem.toLowerCase()) return false;
    return true;
  });
}

function getKnownProjects(upload: UploadRecord | null): string[] {
  const layout = layoutState(upload);
  return uniqueStrings([
    ...asStringArray(layout.pending_projects),
    ...Object.keys(asStringMap(layout.auto_assignments)),
    ...objectKeys(uploadState(upload).dedup_project_keys),
  ]);
}

function getAutoAssignments(upload: UploadRecord | null): Record<string, string> {
  return asStringMap(layoutState(upload).auto_assignments);
}

function getExistingClassifications(upload: UploadRecord | null): Record<string, string> {
  return asStringMap(uploadState(upload).classifications);
}

function getExistingProjectTypes(upload: UploadRecord | null): Record<string, string> {
  const state = uploadState(upload);
  return {
    ...asStringMap(state.project_types_auto),
    ...asStringMap(state.project_types_manual),
  };
}

function getAutoDetectedProjectTypes(upload: UploadRecord | null): Record<string, ProjectType> {
  const raw = asStringMap(uploadState(upload).project_types_auto);
  const out: Record<string, ProjectType> = {};
  for (const [projectName, value] of Object.entries(raw)) {
    if (value === "code" || value === "text") out[projectName] = value;
  }
  return out;
}

function getProjectsNeedingType(upload: UploadRecord | null): string[] {
  const state = uploadState(upload);
  return uniqueStrings([...asStringArray(state.project_types_mixed), ...asStringArray(state.project_types_unknown)]);
}

function getDedupCases(upload: UploadRecord | null): DedupCase[] {
  const asks = asRecord(uploadState(upload).dedup_asks);
  return Object.entries(asks).map(([projectName, raw]) => {
    const ask = asRecord(raw);
    const existingProjectName =
      typeof ask.existing === "string" && ask.existing.trim().length > 0 ? ask.existing : "existing project";
    const similarity = typeof ask.similarity === "number" ? Math.round(ask.similarity * 100) : null;
    const pathSimilarity = typeof ask.path_similarity === "number" ? Math.round(ask.path_similarity * 100) : null;
    const fileCount = typeof ask.file_count === "number" ? ask.file_count : null;

    return {
      projectName,
      existingProjectName,
      similarityLabel: similarity !== null ? `${similarity}% match` : undefined,
      pathLabel: pathSimilarity !== null ? `Path ${pathSimilarity}% similar` : undefined,
      filesLabel: fileCount !== null ? `${fileCount} files` : undefined,
    };
  });
}

function getProjectNotes(upload: UploadRecord | null): Record<string, string[]> {
  const notes: Record<string, string[]> = {};

  function addNote(projectName: string, note: string) {
    if (!projectName.trim() || !note.trim()) return;
    if (!notes[projectName]) notes[projectName] = [];
    if (!notes[projectName].includes(note)) notes[projectName].push(note);
  }

  const state = uploadState(upload);
  const asks = asRecord(state.dedup_asks);
  for (const [projectName, raw] of Object.entries(asks)) {
    const existing = asRecord(raw).existing;
    if (typeof existing === "string" && existing.trim().length > 0) {
      addNote(projectName, `Similar to previously analyzed project "${existing}".`);
    } else {
      addNote(projectName, "Similar to a previously analyzed project.");
    }
  }

  const newVersions = asStringMap(state.dedup_new_versions);
  for (const [projectName, existingProject] of Object.entries(newVersions)) {
    addNote(projectName, `Matched to existing project history "${existingProject}" from earlier uploads.`);
  }

  const skipped = asStringArray(state.dedup_skipped_projects);
  for (const projectName of skipped) {
    addNote(projectName, "Already analyzed in a previous upload and skipped here.");
  }

  const warnings = asStringMap(state.dedup_warnings);
  for (const [projectName, warning] of Object.entries(warnings)) {
    addNote(projectName, warning);
  }

  return notes;
}

function isZipFile(file: File): boolean {
  const lowerName = file.name.toLowerCase();
  const lowerType = file.type.toLowerCase();
  return (
    lowerName.endsWith(".zip") ||
    lowerType === "application/zip" ||
    lowerType === "application/x-zip-compressed" ||
    lowerType === "multipart/x-zip"
  );
}

function stageIndexByKey(key: UploadFlowStage): number {
  return STAGES.findIndex((stage) => stage.key === key);
}

export default function UploadPage() {
  const username = getUsername();
  const nav = useNavigate();

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

  const uploadInputRef = useRef<HTMLInputElement | null>(null);

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

  const projectsNeedingType = useMemo(() => getProjectsNeedingType(uploadData), [uploadData]);
  const autoAssignments = useMemo(() => getAutoAssignments(uploadData), [uploadData]);
  const autoDetectedProjectTypes = useMemo(() => getAutoDetectedProjectTypes(uploadData), [uploadData]);

  const dedupCases = useMemo(() => getDedupCases(uploadData), [uploadData]);
  const visibleDedupCases = dedupCases.length > 0 ? dedupCases : persistedDedupCases;
  const currentDedupCase = visibleDedupCases[dedupCaseIndex] ?? null;
  const canGoToPreviousDedupCase = dedupCaseIndex > 0;
  const canGoToNextDedupCase = dedupCaseIndex < visibleDedupCases.length - 1;
  const savedDedupChoices = useMemo(
    () =>
      Object.entries(dedupDecisions).filter(
        (entry): entry is [string, DedupDecision] =>
          entry[1] === "new_project" || entry[1] === "new_version" || entry[1] === "skip",
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

  const completedClassificationCount = useMemo(
    () =>
      classificationProjectsForDisplay.filter(
        (projectName) => Boolean(classifications[projectName]) && Boolean(projectTypes[projectName]),
      ).length,
    [classificationProjectsForDisplay, classifications, projectTypes],
  );

  const dedupResolved = useMemo(
    () => visibleDedupCases.length === 0 || visibleDedupCases.every((entry) => Boolean(dedupDecisions[entry.projectName])),
    [dedupDecisions, visibleDedupCases],
  );

  const allClassificationRowsComplete = useMemo(
    () =>
      classificationProjectsForDisplay.length > 0 &&
      classificationProjectsForDisplay.every(
        (projectName) => Boolean(classifications[projectName]) && Boolean(projectTypes[projectName]),
      ),
    [classificationProjectsForDisplay, classifications, projectTypes],
  );

  const classificationReady = useMemo(() => {
    if (!uploadData) return false;
    let hasRequirement = false;

    if (needsClassification) {
      hasRequirement = true;
      if (knownProjects.length === 0) return false;
      for (const projectName of knownProjects) {
        const linkedSource = newVersionSourceByTarget[projectName];
        const value = classifications[projectName] || (linkedSource ? classifications[linkedSource] : "");
        if (!value) return false;
      }
    }

    if (needsProjectTypes) {
      hasRequirement = true;
      if (projectsNeedingType.length === 0) return false;
      for (const projectName of projectsNeedingType) {
        const linkedSource = newVersionSourceByTarget[projectName];
        const value = projectTypes[projectName] || (linkedSource ? projectTypes[linkedSource] : "");
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
    projectTypes,
    projectsNeedingType,
    uploadData,
  ]);

  const primaryLabel = useMemo(() => {
    if (isSubmitting) {
      if (currentStage.key === "upload") return "Uploading...";
      return "Saving...";
    }

    if (currentStage.key === "classification") {
      if (uploadData && !needsClassification && !needsProjectTypes && allClassificationRowsComplete) return "Completed";
      return "Submit and Continue";
    }

    if (currentStage.key === "deduplication") return "Resolve and Continue";
    return "Next";
  }, [allClassificationRowsComplete, currentStage.key, isSubmitting, needsClassification, needsProjectTypes, uploadData]);

  const primaryDisabled = useMemo(() => {
    if (isSubmitting) return true;

    if (currentStage.key === "upload") return !selectedFile;
    if (currentStage.key === "projects") return !uploadData || discoveredProjects.length === 0;
    if (currentStage.key === "deduplication") return !uploadData || !dedupResolved;

    if (!uploadData) return true;
    if (!allClassificationRowsComplete) return true;
    if (!needsClassification && !needsProjectTypes) return false;
    return !classificationReady;
  }, [
    allClassificationRowsComplete,
    classificationReady,
    currentStage.key,
    dedupResolved,
    discoveredProjects.length,
    isSubmitting,
    needsClassification,
    needsProjectTypes,
    selectedFile,
    uploadData,
  ]);

  const sidebarNextDisabled = useMemo(() => {
    if (isSubmitting) return true;
    if (!uploadData) return true;
    if (uploadData.status === "failed") return true;
    return (
      uploadData.status === "needs_dedup" ||
      uploadData.status === "needs_classification" ||
      uploadData.status === "needs_project_types"
    );
  }, [isSubmitting, uploadData]);

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "active" as const },
    { label: "3. Setup", status: "disabled" as const, disabled: true },
  ];

  const sizeLabel = selectedFile ? `${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB` : null;

  useEffect(() => {
    if (dedupCases.length > 0) {
      setPersistedDedupCases(dedupCases);
    }
  }, [dedupCases]);

  useEffect(() => {
    setDedupCaseIndex(0);
    const existingDecisions = asStringMap(uploadState(uploadData).dedup_resolved);
    setDedupDecisions((prev) => {
      const next = { ...prev };
      for (const [projectName, value] of Object.entries(existingDecisions)) {
        if (value === "new_project" || value === "new_version" || value === "skip") {
          next[projectName] = value;
        }
      }
      return next;
    });

    const seededClassifications = {
      ...asStringMap(autoAssignments),
      ...asStringMap(getExistingClassifications(uploadData)),
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

    const seededTypes = asStringMap(getExistingProjectTypes(uploadData));
    setProjectTypes((prev) => {
      const next = { ...prev };
      for (const [projectName, value] of Object.entries(seededTypes)) {
        if (value === "code" || value === "text") {
          next[projectName] = value;
        }
      }
      return next;
    });
  }, [autoAssignments, uploadData]);

  useEffect(() => {
    if (dedupCaseIndex <= visibleDedupCases.length - 1) return;
    setDedupCaseIndex(0);
  }, [dedupCaseIndex, visibleDedupCases.length]);

  function resetFlowForNewFile(file: File | null) {
    setSelectedFile(file);
    setUploadData(null);
    setSubmitError(null);
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

  async function onProgressStepClick(targetIndex: number) {
    if (isSubmitting) return;

    if (targetIndex <= stageIndex) {
      setStageIndex(targetIndex);
      return;
    }

    if (targetIndex !== stageIndex + 1) return;

    const stageKey = STAGES[stageIndex]?.key;
    if (!stageKey) return;

    if (stageKey === "upload") await handleUploadNext();
    else if (stageKey === "projects") handleProjectsNext();
    else if (stageKey === "deduplication") await handleDedupNext();
    else await handleClassificationNext();
  }

  function unlockAndGoTo(stageKey: UploadFlowStage) {
    const idx = stageIndexByKey(stageKey);
    setStageIndex(idx);
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
      unlockAndGoTo("projects");
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

    setSubmitError(null);
    unlockAndGoTo("deduplication");
    return true;
  }

  async function handleDedupNext(): Promise<boolean> {
    if (!uploadData) return false;

    setSubmitError(null);

    if (visibleDedupCases.length === 0) {
      unlockAndGoTo("classification");
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
      unlockAndGoTo("classification");
      return true;
    }

    setIsSubmitting(true);
    try {
      const response = await postUploadDedupResolve(uploadData.upload_id, decisions);
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "Failed to save deduplication decisions.");
      }
      setUploadData(response.data);
      unlockAndGoTo("classification");
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

    if (!needsClassification && !needsProjectTypes) {
      return true;
    }

    let workingUpload = uploadData;
    setIsSubmitting(true);

    try {
      if (workingUpload.status === "needs_classification") {
        const targets = getKnownProjects(workingUpload);
        const assignments: Record<string, ProjectClassification> = {};

        if (targets.length === 0) {
          throw new Error("No projects available for classification.");
        }

        for (const projectName of targets) {
          const linkedSource = newVersionSourceByTarget[projectName];
          const value = classifications[projectName] || (linkedSource ? classifications[linkedSource] : "");
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

      if (workingUpload.status === "needs_project_types") {
        const neededProjects = getProjectsNeedingType(workingUpload);
        const project_types: Record<string, ProjectType> = {};

        for (const projectName of neededProjects) {
          const linkedSource = newVersionSourceByTarget[projectName];
          const value = projectTypes[projectName] || (linkedSource ? projectTypes[linkedSource] : "");
          if (value !== "code" && value !== "text") {
            throw new Error(`Please choose a project type for ${projectName}.`);
          }
          project_types[projectName] = value;
        }

        const response = await postUploadProjectTypes(workingUpload.upload_id, project_types);
        if (!response.success || !response.data) {
          throw new Error(response.error?.message ?? "Failed to save project types.");
        }
        workingUpload = response.data;
      }

      setUploadData(workingUpload);
      return true;
    } catch (e: unknown) {
      setSubmitError(e instanceof Error ? e.message : "Failed to save classification data.");
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onPrimaryAction() {
    if (primaryDisabled) return;

    if (currentStage.key === "upload") await handleUploadNext();
    else if (currentStage.key === "projects") handleProjectsNext();
    else if (currentStage.key === "deduplication") await handleDedupNext();
    else await handleClassificationNext();
  }

  function onSidebarNext() {
    if (sidebarNextDisabled) return;
    nav("/upload/setup");
  }

  function handleFileSelect(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    selectZipFile(file);
    if (file && !isZipFile(file)) {
      event.target.value = "";
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0] ?? null;
    selectZipFile(file);
  }

  function renderUploadStage() {
    return (
      <div className="uploadStagePanel">
        <h2 className="wizardPlaceholderTitle">Upload</h2>

        <div className="uploadIntroRow">
          <div className="uploadIntroText">
            <p>Only ZIP files are accepted.</p>
            <p>
              We treat each folder inside a zip file as one project. Optionally, you can organize projects under{" "}
              <code>individual/</code> and <code>collaborative/</code>, then place project folders inside those.
            </p>
            <p>
              If you use <code>individual/</code> and <code>collaborative/</code>, classification can be auto-detected.
              If not, we&apos;ll ask classification during upload.
            </p>
            <p>
              After upload, projects are compared with other projects in the same or previous uploads to detect duplicates
              or existing history.
            </p>
          </div>

          <div className="uploadStructureCard" aria-label="Upload structure example">
            <div className="uploadStructureTitle">Example ZIP structure</div>
            <pre className="uploadStructurePre">
{`projects.zip
    individual/
        ProjectA/
        ProjectB/
    collaborative/
        ProjectC/`}
            </pre>
          </div>
        </div>

        <input
          ref={uploadInputRef}
          type="file"
          accept=".zip,application/zip,application/x-zip-compressed"
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

  function renderDedupStage() {
    function dedupLabel(choice: DedupDecision): string {
      if (choice === "new_project") return "New project";
      if (choice === "new_version") return "New version";
      return "Skip";
    }

    return (
      <div className="dedupStagePanel">
        <h2 className="wizardPlaceholderTitle">Deduplication</h2>
        <p className="wizardPlaceholderText">Review similar projects one-by-one and choose how each should be treated.</p>

        {visibleDedupCases.length === 0 ? (
          savedDedupChoices.length === 0 ? (
            <div className="uploadEmptyState">No deduplication found.</div>
          ) : (
            <div className="dedupSavedPanel">
              <div className="dedupSavedTitle">Saved decisions</div>
              <ul className="dedupSavedList">
                {savedDedupChoices.map(([projectName, choice]) => (
                  <li key={projectName} className="dedupSavedItem">
                    <strong>{projectName}</strong>: {dedupLabel(choice)}
                  </li>
                ))}
              </ul>
            </div>
          )
        ) : (
          <>
            <div className="dedupStageCaseCount">
              Case {dedupCaseIndex + 1} of {visibleDedupCases.length}
            </div>

            {currentDedupCase && (
              <div className="dedupStageCard">
                <div className="dedupStageSummary">
                  Project "{currentDedupCase.projectName}" looks related to "{currentDedupCase.existingProjectName}".
                </div>

                <div className="dedupStageBadges">
                  {currentDedupCase.similarityLabel && <span className="dedupStageBadge">{currentDedupCase.similarityLabel}</span>}
                  {currentDedupCase.pathLabel && <span className="dedupStageBadge">{currentDedupCase.pathLabel}</span>}
                  {currentDedupCase.filesLabel && <span className="dedupStageBadge">{currentDedupCase.filesLabel}</span>}
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

                <label className="dedupStageOption">
                  <input
                    type="radio"
                    name={`dedup-${currentDedupCase.projectName}`}
                    value="skip"
                    checked={dedupDecisions[currentDedupCase.projectName] === "skip"}
                    onChange={() => setDedupDecisions((prev) => ({ ...prev, [currentDedupCase.projectName]: "skip" }))}
                  />
                  <span>Skip this project</span>
                </label>
              </div>
            )}

            {savedDedupChoices.length > 0 && (
              <div className="dedupSavedPanel">
                <div className="dedupSavedTitle">Saved decisions</div>
                <ul className="dedupSavedList">
                  {savedDedupChoices.map(([projectName, choice]) => (
                    <li key={projectName} className="dedupSavedItem">
                      <strong>{projectName}</strong>: {dedupLabel(choice)}
                    </li>
                  ))}
                </ul>
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
    function readableClassification(value: ProjectClassificationValue | undefined) {
      if (value === "individual") return "Individual";
      if (value === "collaborative") return "Collaborative";
      return "";
    }

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
                          value={classifications[projectName] ?? ""}
                          onChange={(event) =>
                            setClassifications((prev) => ({
                              ...prev,
                              [projectName]: event.target.value as ProjectClassificationValue,
                            }))
                          }
                        >
                          <option value="">Select</option>
                          <option value="individual">Individual</option>
                          <option value="collaborative">Collaborative</option>
                        </select>
                        {autoAssignments[projectName] && (
                          <div className="classificationStageHint">
                            Auto-detected: {readableClassification(classifications[projectName])}
                          </div>
                        )}
                      </td>
                      <td>
                        <select
                          className="classificationStageSelect"
                          value={projectTypes[projectName] ?? ""}
                          onChange={(event) =>
                            setProjectTypes((prev) => ({
                              ...prev,
                              [projectName]: event.target.value as ProjectTypeValue,
                            }))
                          }
                        >
                          <option value="">Select</option>
                          <option value="text">Text</option>
                          <option value="code">Code</option>
                        </select>
                        {autoDetectedProjectTypes[projectName] && (
                          <div className="classificationStageHint">
                            Auto-detected: {autoDetectedProjectTypes[projectName] === "code" ? "Code" : "Text"}
                          </div>
                        )}
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
      actionLabel="Next"
      onAction={onSidebarNext}
      actionDisabled={sidebarNextDisabled}
      showAction
    >
      <div className="wizardPlaceholderCard">
        <div className="uploadStageProgress" aria-label="Upload flow progress">
          <div className="uploadStageProgressMeta">
            <span>
              Step {stageIndex + 1} of {STAGES.length}
            </span>
            <div className="uploadStageProgressStepNav" role="tablist" aria-label="Upload flow steps">
              {STAGES.map((stage, idx) => (
                <button
                  key={stage.key}
                  type="button"
                  role="tab"
                  aria-selected={idx === stageIndex}
                  className={`uploadStageProgressStepBtn${
                    idx < stageIndex ? " uploadStageProgressStepBtn--done" : ""
                  }${idx === stageIndex ? " uploadStageProgressStepBtn--active" : ""}`}
                  disabled={isSubmitting}
                  onClick={() => onProgressStepClick(idx)}
                >
                  {idx + 1}. {stage.label}
                </button>
              ))}
            </div>
          </div>
          <div className="uploadStageProgressTrack">
            <div className="uploadStageProgressFill" style={{ width: `${stageProgressPercent}%` }} />
          </div>
        </div>

        {submitError && <p className="error uploadStatusLine">{submitError}</p>}
        {renderStageBody()}

        <div className="uploadStageActionRow">
          <button type="button" className="uploadStageBackBtn" onClick={onBack} disabled={!canGoBack || isSubmitting}>
            Back
          </button>

          <button type="button" className="uploadStagePrimaryBtn" onClick={onPrimaryAction} disabled={primaryDisabled}>
            {primaryLabel}
          </button>
        </div>
      </div>
    </UploadWizardShell>
  );
}
