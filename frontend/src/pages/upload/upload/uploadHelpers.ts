import type { ProjectType, UploadRecord } from "../../../api/uploads";
import type { DedupCase, ProjectClassificationValue, ProjectTypeValue } from "./uploadTypes";

export function asRecord(value: unknown): Record<string, unknown> {
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

export function asStringArray(value: unknown): string[] {
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

export function asStringMap(value: unknown): Record<string, string> {
  const out: Record<string, string> = {};
  const obj = asRecord(value);
  for (const [k, v] of Object.entries(obj)) {
    if (typeof v === "string" && v.trim().length > 0) out[k] = v;
  }
  return out;
}

export function objectKeys(value: unknown): string[] {
  return Object.keys(asRecord(value)).filter((key) => key.trim().length > 0);
}

export function uniqueStrings(items: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const item of items) {
    if (seen.has(item)) continue;
    seen.add(item);
    out.push(item);
  }
  return out;
}

export function uploadState(upload: UploadRecord | null): Record<string, unknown> {
  return asRecord(upload?.state);
}

export function layoutState(upload: UploadRecord | null): Record<string, unknown> {
  return asRecord(uploadState(upload).layout);
}

export function getProjectsFromUpload(upload: UploadRecord | null): string[] {
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

export function getDiscoveredProjects(upload: UploadRecord | null): string[] {
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

export function getKnownProjects(upload: UploadRecord | null): string[] {
  const layout = layoutState(upload);
  return uniqueStrings([
    ...asStringArray(layout.pending_projects),
    ...Object.keys(asStringMap(layout.auto_assignments)),
    ...objectKeys(uploadState(upload).dedup_project_keys),
  ]);
}

export function getAutoAssignments(upload: UploadRecord | null): Record<string, string> {
  return asStringMap(layoutState(upload).auto_assignments);
}

export function getExistingClassifications(upload: UploadRecord | null): Record<string, string> {
  return asStringMap(uploadState(upload).classifications);
}

export function getExistingProjectTypes(upload: UploadRecord | null): Record<string, string> {
  const state = uploadState(upload);
  return {
    ...asStringMap(state.project_types_auto),
    ...asStringMap(state.project_types_manual),
  };
}

export function getAutoDetectedProjectTypes(upload: UploadRecord | null): Record<string, ProjectType> {
  const state = uploadState(upload);
  const raw = asStringMap(state.project_types_auto);
  const out: Record<string, ProjectType> = {};
  for (const [projectName, value] of Object.entries(raw)) {
    if (value === "code" || value === "text") out[projectName] = value;
  }

  const index = asRecord(state.project_filetype_index);
  for (const [projectName, rawFlags] of Object.entries(index)) {
    if (out[projectName]) continue;
    const flags = asRecord(rawFlags);
    const hasCode = Boolean(flags.has_code);
    const hasText = Boolean(flags.has_text);
    if (hasCode && !hasText) out[projectName] = "code";
    else if (!hasCode && hasText) out[projectName] = "text";
  }

  return out;
}

export function getProjectsNeedingType(upload: UploadRecord | null): string[] {
  const state = uploadState(upload);
  return uniqueStrings([...asStringArray(state.project_types_mixed), ...asStringArray(state.project_types_unknown)]);
}

export function toProjectClassificationValue(value: string | undefined): ProjectClassificationValue {
  if (value === "individual" || value === "collaborative") return value;
  return "";
}

export function toProjectTypeValue(value: string | undefined): ProjectTypeValue {
  if (value === "code" || value === "text") return value;
  return "";
}

export function getDedupCases(upload: UploadRecord | null): DedupCase[] {
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

export function getProjectNotes(upload: UploadRecord | null): Record<string, string[]> {
  const notes: Record<string, string[]> = {};

  function addNote(projectName: string, note: string) {
    if (!projectName.trim() || !note.trim()) return;
    if (!notes[projectName]) notes[projectName] = [];
    if (!notes[projectName].includes(note)) notes[projectName].push(note);
  }

  const state = uploadState(upload);
  const layout = layoutState(upload);
  const currentUploadProjects = new Set<string>([
    ...asStringArray(layout.pending_projects),
    ...Object.keys(asStringMap(layout.auto_assignments)),
  ]);

  const asks = asRecord(state.dedup_asks);
  for (const [projectName, raw] of Object.entries(asks)) {
    const existing = asRecord(raw).existing;
    if (typeof existing === "string" && existing.trim().length > 0) {
      if (existing !== projectName && currentUploadProjects.has(existing)) {
        addNote(projectName, `Similar to another project in this upload "${existing}".`);
      } else {
        addNote(projectName, `Similar to previously analyzed project "${existing}".`);
      }
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

export function isZipFile(file: File): boolean {
  const lowerName = file.name.toLowerCase();
  const lowerType = file.type.toLowerCase();
  return (
    lowerName.endsWith(".zip") ||
    lowerType === "application/zip" ||
    lowerType === "application/x-zip-compressed" ||
    lowerType === "multipart/x-zip"
  );
}
