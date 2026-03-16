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
  const { classification, projectType, mainFile } = args;

  if (projectType === "code") {
    return { label: "ready for analysis", tone: "ready" };
  }

  if (projectType === "text") {
    return mainFile
      ? { label: "ready for analysis", tone: "ready" }
      : { label: "main file missing", tone: "warning" };
  }

  if (!classification) {
    return { label: "classification missing", tone: "warning" };
  }

  return { label: "setup in progress", tone: "neutral" };
}
