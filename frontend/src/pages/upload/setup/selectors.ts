import type { ProjectClassification, ProjectType, UploadRecord } from "../../../api/uploads";
import { resolveSetupStatus } from "./rules";
import type { SetupProjectCard } from "./types";

function asRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return value as Record<string, unknown>;
}

function asStringMap(value: unknown): Record<string, string> {
  const out: Record<string, string> = {};
  const obj = asRecord(value);
  for (const [key, item] of Object.entries(obj)) {
    if (typeof item === "string" && item.trim()) out[key] = item;
  }
  return out;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function asNumberArray(value: unknown): number[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => (typeof item === "number" ? item : Number.NaN))
    .filter((item) => Number.isInteger(item) && item > 0);
}

function readProjectKey(value: unknown): number | null {
  if (typeof value === "number" && Number.isInteger(value) && value > 0) return value;
  if (typeof value === "string" && /^\d+$/.test(value)) return Number.parseInt(value, 10);
  return null;
}

function normalizeClassification(value: string): ProjectClassification | "" {
  if (value === "individual" || value === "collaborative") return value;
  return "";
}

function normalizeProjectType(value: string): ProjectType | "" {
  if (value === "code" || value === "text") return value;
  return "";
}

export function toProjectTypeLabel(projectType: ProjectType | ""): string {
  if (projectType === "code") return "Code Project";
  if (projectType === "text") return "Text Project";
  return "Type TBD";
}

export function deriveProjectCards(upload: UploadRecord | null): SetupProjectCard[] {
  if (!upload) return [];

  const state = asRecord(upload.state);

  const dedupProjectKeys = asRecord(state.dedup_project_keys);
  const classifications = asStringMap(state.classifications);
  const projectTypesAuto = asStringMap(state.project_types_auto);
  const projectTypesManual = asStringMap(state.project_types_manual);
  const fileRoles = asRecord(state.file_roles);
  const contributions = asRecord(state.contributions);
  const runInputsProjects = asRecord(asRecord(state.run_inputs).projects);

  const projectNames = new Set<string>([
    ...Object.keys(dedupProjectKeys),
    ...Object.keys(classifications),
    ...Object.keys(projectTypesAuto),
    ...Object.keys(projectTypesManual),
  ]);

  return Array.from(projectNames)
    .filter((name) => name.trim().length > 0)
    .sort((a, b) => a.localeCompare(b))
    .map((projectName) => {
      const projectKey = readProjectKey(dedupProjectKeys[projectName]);
      const classification = normalizeClassification(classifications[projectName] ?? "");
      const projectType = normalizeProjectType(
        projectTypesManual[projectName] ?? projectTypesAuto[projectName] ?? "",
      );

      const projectRunInput = asRecord(runInputsProjects[projectName]);
      const capabilities = asRecord(projectRunInput.capabilities);
      const git = asRecord(capabilities.git);
      const integrations = asRecord(projectRunInput.integrations);
      const github = asRecord(integrations.github);
      const drive = asRecord(integrations.drive);
      const repoDetectedRaw = git.repo_detected;
      const gitRepoDetected = typeof repoDetectedRaw === "boolean" ? repoDetectedRaw : null;
      const gitCommitCountHint = typeof git.commit_count_hint === "number" ? git.commit_count_hint : 0;
      const gitAuthorCountHint = typeof git.author_count_hint === "number" ? git.author_count_hint : 0;
      const gitMultiAuthorHint = Boolean(git.multi_author_hint);
      const gitSelectedIdentityIndices = asNumberArray(git.selected_identity_indices);

      const repoLinked = Boolean(github.repo_linked);
      const githubState =
        typeof github.state === "string" && github.state.trim()
          ? github.state.trim().toLowerCase()
          : "unset";
      const githubRepoFullName =
        typeof github.repo_full_name === "string" && github.repo_full_name.trim()
          ? github.repo_full_name.trim()
          : null;

      const driveState =
        typeof drive.state === "string" && drive.state.trim()
          ? drive.state.trim().toLowerCase()
          : "unset";
      const driveLinkedFilesCount =
        typeof drive.linked_files_count === "number" ? drive.linked_files_count : 0;

      const roleForProject = asRecord(fileRoles[projectName]);
      const mainFileFromRoles = typeof roleForProject.main_file === "string" ? roleForProject.main_file.trim() : "";

      const keyContrib =
        projectKey !== null
          ? asRecord(contributions[String(projectKey)])
          : {};
      const nameContrib = asRecord(contributions[projectName]);
      const projectContrib = {
        ...keyContrib,
        ...nameContrib,
      };

      const mainFileFromContrib =
        typeof projectContrib.main_file === "string" ? projectContrib.main_file.trim() : "";
      const mainFile = mainFileFromRoles || mainFileFromContrib;
      const mainSectionIds = asNumberArray(projectContrib.main_section_ids);
      const supportingTextRelpaths = asStringArray(projectContrib.supporting_text_relpaths);
      const supportingCsvRelpaths = asStringArray(projectContrib.supporting_csv_relpaths);

      const status = resolveSetupStatus({
        classification,
        projectType,
        repoLinked,
        mainFile,
      });

      return {
        projectName,
        projectKey,
        classification,
        projectType,
        gitRepoDetected,
        gitCommitCountHint,
        gitAuthorCountHint,
        gitMultiAuthorHint,
        gitSelectedIdentityIndices,
        githubState,
        githubRepoLinked: repoLinked,
        githubRepoFullName,
        mainFileRelpath: mainFile || null,
        mainSectionIds,
        supportingTextRelpaths,
        supportingCsvRelpaths,
        driveState,
        driveLinkedFilesCount,
        statusLabel: status.label,
        statusTone: status.tone,
      };
    });
}
