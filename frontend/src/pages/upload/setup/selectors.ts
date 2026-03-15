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
      const classification = normalizeClassification(classifications[projectName] ?? "");
      const projectType = normalizeProjectType(
        projectTypesManual[projectName] ?? projectTypesAuto[projectName] ?? "",
      );

      const projectRunInput = asRecord(runInputsProjects[projectName]);
      const integrations = asRecord(projectRunInput.integrations);
      const github = asRecord(integrations.github);
      const repoLinked = Boolean(github.repo_linked);

      const roleForProject = asRecord(fileRoles[projectName]);
      const mainFile = typeof roleForProject.main_file === "string" ? roleForProject.main_file.trim() : "";

      const status = resolveSetupStatus({
        classification,
        projectType,
        repoLinked,
        mainFile,
      });

      return {
        projectName,
        projectKey: readProjectKey(dedupProjectKeys[projectName]),
        classification,
        projectType,
        statusLabel: status.label,
        statusTone: status.tone,
      };
    });
}
