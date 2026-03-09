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
