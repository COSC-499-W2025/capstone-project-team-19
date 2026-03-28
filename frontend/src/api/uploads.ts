import { api } from "./client";

export type ApiError = {
  message: string;
  code: number;
};

export type ApiResponse<T> = {
  success: boolean;
  data: T | null;
  error: ApiError | null;
};

export type UploadStatus =
  | "started"
  | "parsed"
  | "needs_dedup"
  | "needs_classification"
  | "needs_project_types"
  | "needs_file_roles"
  | "needs_summaries"
  | "analyzing"
  | "done"
  | "failed";

export type UploadRecord = {
  upload_id: number;
  status: UploadStatus;
  zip_name: string | null;
  state: Record<string, unknown>;
};

export type DedupDecision = "skip" | "new_project" | "new_version";
export type ProjectClassification = "individual" | "collaborative";
export type ProjectType = "code" | "text";
export type RunScope = "all" | "individual" | "collaborative";
export type RunMode = "run" | "check";

export type UploadFileItem = {
  relpath: string;
  file_name: string;
  file_type: string | null;
  extension: string | null;
  size_bytes: number | null;
};

export type UploadProjectFilesRecord = {
  project_key: number | null;
  version_key: number | null;
  project_name: string;
  all_files: UploadFileItem[];
  text_files: UploadFileItem[];
  csv_files: UploadFileItem[];
};

export type MainFileSection = {
  id: number;
  title: string;
  preview: string;
  content: string;
  is_truncated: boolean;
};

export type MainFileSectionsRecord = {
  project_key: number | null;
  version_key: number | null;
  project_name: string;
  main_file: string;
  sections: MainFileSection[];
};

export type GitIdentityOption = {
  index: number;
  name: string | null;
  email: string | null;
  commit_count: number;
};

export type GitIdentitiesRecord = {
  options: GitIdentityOption[];
  selected_indices: number[];
};

export type RunWarning = {
  code: string;
  project?: string;
  [key: string]: unknown;
};

export type RunErrorDetail = {
  code: string;
  project?: string;
  projects?: string[];
  scope?: RunScope;
  status?: string;
  [key: string]: unknown;
};

export type RunPreflightRecord = {
  upload_id: number;
  scope: RunScope;
  ready: boolean;
  warnings: RunWarning[];
  errors: RunErrorDetail[];
};

export type GitHubStartRecord = {
  auth_url: string | null;
};

export type GitHubRepo = {
  full_name: string;
};

export type GitHubReposRecord = {
  repos: GitHubRepo[];
};

export type GitHubLinkRecord = {
  success: boolean;
  repo_full_name?: string;
  [key: string]: unknown;
};

export type DriveStartRecord = {
  auth_url: string | null;
};

export type DriveFile = {
  id: string;
  name: string;
  mime_type: string;
};

export type DriveFilesRecord = {
  files: DriveFile[];
};

export type DriveLinkItemRequest = {
  local_file_name: string;
  drive_file_id: string;
  drive_file_name: string;
  mime_type: string;
};

export type DriveLinkRecord = {
  success: boolean;
  project_name?: string;
  files_linked?: number;
  [key: string]: unknown;
};

function toProjectPathSegment(projectName: string): string {
  return encodeURIComponent(projectName);
}

export async function postProjectsUpload(file: File | Blob, filename = "upload.zip") {
  const formData = new FormData();
  formData.append("file", file, filename);
  return api.postForm<ApiResponse<UploadRecord>>("/projects/upload", formData);
}

export async function postUploadDedupResolve(uploadId: number, decisions: Record<string, DedupDecision>) {
  return api.postJson<ApiResponse<UploadRecord>>(`/projects/upload/${uploadId}/dedup/resolve`, { decisions });
}

export async function postUploadClassifications(uploadId: number, assignments: Record<string, ProjectClassification>) {
  return api.postJson<ApiResponse<UploadRecord>>(`/projects/upload/${uploadId}/classifications`, { assignments });
}

export async function postUploadProjectTypes(uploadId: number, project_types: Record<string, ProjectType>) {
  return api.postJson<ApiResponse<UploadRecord>>(`/projects/upload/${uploadId}/project-types`, { project_types });
}

export async function getUploadStatus(uploadId: number) {
  return api.get<ApiResponse<UploadRecord>>(`/projects/upload/${uploadId}`);
}

export async function deleteUpload(uploadId: number) {
  return api.delete<ApiResponse<null>>(`/projects/upload/${uploadId}`);
}

export async function getUploadProjectFiles(uploadId: number, projectKey: number) {
  return api.get<ApiResponse<UploadProjectFilesRecord>>(`/projects/upload/${uploadId}/projects/${projectKey}/files`);
}

export async function postUploadProjectMainFile(uploadId: number, projectKey: number, relpath: string) {
  return api.postJson<ApiResponse<UploadRecord>>(
    `/projects/upload/${uploadId}/projects/${projectKey}/main-file`,
    { relpath },
  );
}

export async function getUploadProjectTextSections(uploadId: number, projectKey: number) {
  return api.get<ApiResponse<MainFileSectionsRecord>>(`/projects/upload/${uploadId}/projects/${projectKey}/text/sections`);
}

export async function postUploadProjectTextContributions(uploadId: number, projectKey: number, selected_section_ids: number[]) {
  return api.postJson<ApiResponse<UploadRecord>>(
    `/projects/upload/${uploadId}/projects/${projectKey}/text/contributions`,
    { selected_section_ids },
  );
}

export async function postUploadProjectSupportingTextFiles(uploadId: number, projectKey: number, relpaths: string[]) {
  return api.postJson<ApiResponse<UploadRecord>>(
    `/projects/upload/${uploadId}/projects/${projectKey}/supporting-text-files`,
    { relpaths },
  );
}

export async function postUploadProjectSupportingCsvFiles(uploadId: number, projectKey: number, relpaths: string[]) {
  return api.postJson<ApiResponse<UploadRecord>>(
    `/projects/upload/${uploadId}/projects/${projectKey}/supporting-csv-files`,
    { relpaths },
  );
}

export async function postUploadProjectKeyRole(uploadId: number, projectKey: number, key_role: string) {
  return api.postJson<ApiResponse<UploadRecord>>(
    `/projects/upload/${uploadId}/projects/${projectKey}/key-role`,
    { key_role },
  );
}

export async function getUploadProjectGitIdentities(uploadId: number, projectKey: number) {
  return api.get<ApiResponse<GitIdentitiesRecord>>(`/projects/upload/${uploadId}/projects/${projectKey}/git/identities`);
}

export async function postUploadProjectGitIdentities(
  uploadId: number,
  projectKey: number,
  selected_indices: number[],
  extra_emails: string[] = [],
) {
  return api.postJson<ApiResponse<GitIdentitiesRecord>>(
    `/projects/upload/${uploadId}/projects/${projectKey}/git/identities`,
    { selected_indices, extra_emails },
  );
}

export async function postUploadProjectManualProjectSummary(uploadId: number, projectKey: number, summary_text: string) {
  return api.postJson<ApiResponse<UploadRecord>>(
    `/projects/upload/${uploadId}/projects/${projectKey}/manual-project-summary`,
    { summary_text },
  );
}

export async function postUploadProjectManualContributionSummary(
  uploadId: number,
  projectKey: number,
  manual_contribution_summary: string,
) {
  return api.postJson<ApiResponse<UploadRecord>>(
    `/projects/upload/${uploadId}/projects/${projectKey}/manual-contribution-summary`,
    { manual_contribution_summary },
  );
}

export async function postUploadRun(
  uploadId: number,
  payload: { scope?: RunScope; force_rerun?: boolean; mode?: RunMode } = {},
) {
  const {
    scope = "all",
    force_rerun = false,
    mode = "run",
  } = payload;
  return api.postJson<ApiResponse<RunPreflightRecord>>(`/projects/upload/${uploadId}/run`, {
    scope,
    force_rerun,
    mode,
  });
}

export async function postUploadProjectGithubStart(uploadId: number, projectName: string, connect_now: boolean) {
  const project = toProjectPathSegment(projectName);
  return api.postJson<ApiResponse<GitHubStartRecord>>(
    `/projects/upload/${uploadId}/projects/${project}/github/start`,
    { connect_now },
  );
}

export async function getUploadProjectGithubRepos(uploadId: number, projectName: string) {
  const project = toProjectPathSegment(projectName);
  return api.get<ApiResponse<GitHubReposRecord>>(`/projects/upload/${uploadId}/projects/${project}/github/repos`);
}

export async function postUploadProjectGithubLink(uploadId: number, projectName: string, repo_full_name: string) {
  const project = toProjectPathSegment(projectName);
  return api.postJson<ApiResponse<GitHubLinkRecord>>(
    `/projects/upload/${uploadId}/projects/${project}/github/link`,
    { repo_full_name },
  );
}

export async function postUploadProjectDriveStart(uploadId: number, projectName: string, connect_now: boolean) {
  const project = toProjectPathSegment(projectName);
  return api.postJson<ApiResponse<DriveStartRecord>>(
    `/projects/upload/${uploadId}/projects/${project}/drive/start`,
    { connect_now },
  );
}

export async function getUploadProjectDriveFiles(uploadId: number, projectName: string) {
  const project = toProjectPathSegment(projectName);
  return api.get<ApiResponse<DriveFilesRecord>>(`/projects/upload/${uploadId}/projects/${project}/drive/files`);
}

export async function postUploadProjectDriveLink(uploadId: number, projectName: string, links: DriveLinkItemRequest[]) {
  const project = toProjectPathSegment(projectName);
  return api.postJson<ApiResponse<DriveLinkRecord>>(
    `/projects/upload/${uploadId}/projects/${project}/drive/link`,
    { links },
  );
}
