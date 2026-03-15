import type { ProjectClassification, ProjectType, UploadRecord } from "../../../api/uploads";

export type SetupBadgeTone = "ready" | "warning" | "neutral";

export type SetupProjectCard = {
  projectName: string;
  projectKey: number | null;
  classification: ProjectClassification | "";
  projectType: ProjectType | "";
  statusLabel: string;
  statusTone: SetupBadgeTone;
};

export type SetupFlowResult = {
  upload: UploadRecord | null;
  hasValidUploadId: boolean;
  uploadId: number | null;
  loading: boolean;
  loadError: string | null;
  uploadNotFound: boolean;
  projectCards: SetupProjectCard[];
  individualProjects: SetupProjectCard[];
  collaborativeProjects: SetupProjectCard[];
  expandedProjectName: string | null;
  onToggleProject: (projectName: string) => void;
};
