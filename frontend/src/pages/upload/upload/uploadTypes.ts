import type { DedupDecision, ProjectClassification, ProjectType } from "../../../api/uploads";

export type UploadFlowStage = "upload" | "projects" | "deduplication" | "classification";

export type StageDef = {
  key: UploadFlowStage;
  label: string;
};

export type DedupDecisionValue = "" | DedupDecision;
export type VisibleDedupDecision = Exclude<DedupDecision, "skip">;
export type ProjectClassificationValue = "" | ProjectClassification;
export type ProjectTypeValue = "" | ProjectType;

export type DedupCase = {
  projectName: string;
  existingProjectName: string;
  similarityLabel?: string;
  pathLabel?: string;
  filesLabel?: string;
};

export type ProjectNote = {
  text: string;
  linkedProjectName?: string;
};

export const STAGES: StageDef[] = [
  { key: "upload", label: "Upload" },
  { key: "projects", label: "Projects" },
  { key: "deduplication", label: "Deduplication" },
  { key: "classification", label: "Classification" },
];
