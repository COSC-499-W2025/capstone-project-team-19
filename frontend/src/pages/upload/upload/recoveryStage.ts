import type { UploadListItem } from "../../../api/uploads";

const RECOVERY_STAGE_KEY_PREFIX = "upload-recovery-stage:";

export type UploadRecoveryStage = "upload" | "projects" | "deduplication" | "classification" | "setup";

export function saveUploadRecoveryStage(uploadId: number, stage: UploadRecoveryStage): void {
  if (!uploadId || typeof window === "undefined") return;
  window.localStorage.setItem(`${RECOVERY_STAGE_KEY_PREFIX}${uploadId}`, stage);
}

export function readUploadRecoveryStage(uploadId: number): UploadRecoveryStage | null {
  if (!uploadId || typeof window === "undefined") return null;
  const value = window.localStorage.getItem(`${RECOVERY_STAGE_KEY_PREFIX}${uploadId}`);
  if (
    value === "upload" ||
    value === "projects" ||
    value === "deduplication" ||
    value === "classification" ||
    value === "setup"
  ) {
    return value;
  }
  return null;
}

export function clearUploadRecoveryStage(uploadId: number | null | undefined): void {
  if (!uploadId || typeof window === "undefined") return;
  window.localStorage.removeItem(`${RECOVERY_STAGE_KEY_PREFIX}${uploadId}`);
}

export function recoveryRouteForUpload(upload: UploadListItem, rememberedStage: UploadRecoveryStage | null): string {
  if (rememberedStage === "setup") {
    return `/upload/setup?uploadId=${upload.upload_id}`;
  }
  if (rememberedStage === "deduplication" || rememberedStage === "classification" || rememberedStage === "projects") {
    return `/upload/upload?uploadId=${upload.upload_id}&stage=${rememberedStage}`;
  }
  if (rememberedStage === "upload") {
    return `/upload/upload?uploadId=${upload.upload_id}&stage=projects`;
  }

  if (upload.status === "needs_file_roles" || upload.status === "needs_summaries") {
    return `/upload/setup?uploadId=${upload.upload_id}`;
  }
  if (upload.status === "needs_dedup") {
    return `/upload/upload?uploadId=${upload.upload_id}&stage=deduplication`;
  }
  if (upload.status === "started" || upload.status === "parsed") {
    return `/upload/upload?uploadId=${upload.upload_id}&stage=projects`;
  }
  return `/upload/upload?uploadId=${upload.upload_id}&stage=classification`;
}
