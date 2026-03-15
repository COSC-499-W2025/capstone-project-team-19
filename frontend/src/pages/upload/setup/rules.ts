import type { ProjectClassification, ProjectType } from "../../../api/uploads";
import type { SetupBadgeTone } from "./types";

export type SetupStatusResult = {
  label: string;
  tone: SetupBadgeTone;
};

export function isValidUploadIdParam(uploadIdParam: string): boolean {
  return /^[1-9]\d*$/.test(uploadIdParam);
}

export function resolveSetupStatus(args: {
  classification: ProjectClassification | "";
  projectType: ProjectType | "";
  repoLinked: boolean;
  mainFile: string;
}): SetupStatusResult {
  const { classification, projectType, repoLinked, mainFile } = args;

  if (projectType === "code") {
    return repoLinked
      ? { label: "github linked", tone: "ready" }
      : { label: "missing github repo", tone: "warning" };
  }

  if (projectType === "text") {
    return mainFile
      ? { label: "main file selected", tone: "ready" }
      : { label: "main file missing", tone: "warning" };
  }

  if (!classification) {
    return { label: "classification missing", tone: "warning" };
  }

  return { label: "setup in progress", tone: "neutral" };
}
