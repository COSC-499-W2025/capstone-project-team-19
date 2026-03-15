import type {
  DriveFilesRecord,
  DriveLinkItemRequest,
  DriveLinkRecord,
  DriveStartRecord,
  GitHubLinkRecord,
  GitHubReposRecord,
  GitHubStartRecord,
  GitIdentitiesRecord,
  MainFileSectionsRecord,
  ProjectClassification,
  ProjectType,
  UploadStatus,
  RunPreflightRecord,
  UploadProjectFilesRecord,
  UploadRecord,
} from "../../../api/uploads";
import type { ConsentStatusValue } from "../../../api/consent";

export type SetupBadgeTone = "ready" | "warning" | "neutral";

export type SetupProjectCard = {
  projectName: string;
  projectKey: number | null;
  classification: ProjectClassification | "";
  projectType: ProjectType | "";
  gitRepoDetected: boolean | null;
  gitCommitCountHint: number;
  gitAuthorCountHint: number;
  gitMultiAuthorHint: boolean;
  gitSelectedIdentityIndices: number[];
  githubState: string;
  githubRepoLinked: boolean;
  githubRepoFullName: string | null;
  mainFileRelpath: string | null;
  mainSectionIds: number[];
  supportingTextRelpaths: string[];
  supportingCsvRelpaths: string[];
  driveState: string;
  driveLinkedFilesCount: number;
  manualProjectSummary: string;
  manualContributionSummary: string;
  keyRole: string;
  statusLabel: string;
  statusTone: SetupBadgeTone;
  optionalStatusLabel: string | null;
};

export type SetupFlowResult = {
  upload: UploadRecord | null;
  hasValidUploadId: boolean;
  uploadId: number | null;
  uploadStatus: UploadStatus | null;
  externalConsentStatus: ConsentStatusValue | null;
  manualOnlySummaries: boolean;
  loading: boolean;
  isRefreshing: boolean;
  isMutating: boolean;
  loadError: string | null;
  actionError: string | null;
  uploadNotFound: boolean;
  projectCards: SetupProjectCard[];
  individualProjects: SetupProjectCard[];
  collaborativeProjects: SetupProjectCard[];
  expandedProjectNames: string[];
  onToggleProject: (projectName: string) => void;
  clearActionError: () => void;
  refreshUpload: () => Promise<boolean>;
  actions: {
    getProjectFiles: (projectKey: number) => Promise<UploadProjectFilesRecord | null>;
    setMainFile: (projectKey: number, relpath: string) => Promise<UploadRecord | null>;
    getMainFileSections: (projectKey: number) => Promise<MainFileSectionsRecord | null>;
    setContributedSections: (projectKey: number, selectedSectionIds: number[]) => Promise<UploadRecord | null>;
    setSupportingTextFiles: (projectKey: number, relpaths: string[]) => Promise<UploadRecord | null>;
    setSupportingCsvFiles: (projectKey: number, relpaths: string[]) => Promise<UploadRecord | null>;
    setKeyRole: (projectKey: number, keyRole: string) => Promise<UploadRecord | null>;
    getGitIdentities: (projectKey: number) => Promise<GitIdentitiesRecord | null>;
    saveGitIdentities: (
      projectKey: number,
      selectedIndices: number[],
      extraEmails?: string[],
    ) => Promise<GitIdentitiesRecord | null>;
    saveManualProjectSummary: (projectKey: number, summaryText: string) => Promise<UploadRecord | null>;
    saveManualContributionSummary: (
      projectKey: number,
      contributionSummary: string,
    ) => Promise<UploadRecord | null>;
    checkRunReadiness: (scope?: "all" | "individual" | "collaborative") => Promise<RunPreflightRecord | null>;
    runAnalysis: (
      scope?: "all" | "individual" | "collaborative",
      forceRerun?: boolean,
    ) => Promise<RunPreflightRecord | null>;
    githubStart: (projectName: string, connectNow: boolean) => Promise<GitHubStartRecord | null>;
    githubRepos: (projectName: string) => Promise<GitHubReposRecord | null>;
    githubLink: (projectName: string, repoFullName: string) => Promise<GitHubLinkRecord | null>;
    driveStart: (projectName: string, connectNow: boolean) => Promise<DriveStartRecord | null>;
    driveFiles: (projectName: string) => Promise<DriveFilesRecord | null>;
    driveLink: (projectName: string, links: DriveLinkItemRequest[]) => Promise<DriveLinkRecord | null>;
  };
};
