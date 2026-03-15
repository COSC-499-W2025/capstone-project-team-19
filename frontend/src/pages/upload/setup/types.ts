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
  RunPreflightRecord,
  UploadProjectFilesRecord,
  UploadRecord,
} from "../../../api/uploads";

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
  isRefreshing: boolean;
  isMutating: boolean;
  loadError: string | null;
  actionError: string | null;
  uploadNotFound: boolean;
  projectCards: SetupProjectCard[];
  individualProjects: SetupProjectCard[];
  collaborativeProjects: SetupProjectCard[];
  expandedProjectName: string | null;
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
    githubStart: (projectName: string, connectNow: boolean) => Promise<GitHubStartRecord | null>;
    githubRepos: (projectName: string) => Promise<GitHubReposRecord | null>;
    githubLink: (projectName: string, repoFullName: string) => Promise<GitHubLinkRecord | null>;
    driveStart: (projectName: string, connectNow: boolean) => Promise<DriveStartRecord | null>;
    driveFiles: (projectName: string) => Promise<DriveFilesRecord | null>;
    driveLink: (projectName: string, links: DriveLinkItemRequest[]) => Promise<DriveLinkRecord | null>;
  };
};
