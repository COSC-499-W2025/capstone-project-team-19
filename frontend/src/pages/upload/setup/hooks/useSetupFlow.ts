import { useCallback, useEffect, useMemo, useState } from "react";
import { getConsentStatus, type ConsentStatusValue } from "../../../../api/consent";
import {
  getUploadProjectDriveFiles,
  getUploadProjectFiles,
  getUploadProjectGithubRepos,
  getUploadProjectGitIdentities,
  getUploadProjectTextSections,
  getUploadStatus,
  postUploadProjectDriveLink,
  postUploadProjectDriveStart,
  postUploadProjectGithubLink,
  postUploadProjectGithubStart,
  postUploadProjectGitIdentities,
  postUploadProjectKeyRole,
  postUploadProjectMainFile,
  postUploadProjectManualContributionSummary,
  postUploadProjectManualProjectSummary,
  postUploadProjectSupportingCsvFiles,
  postUploadProjectSupportingTextFiles,
  postUploadProjectTextContributions,
  postUploadRun,
  type ApiResponse,
  type DriveLinkItemRequest,
  type RunScope,
  type UploadRecord,
} from "../../../../api/uploads";
import { deriveProjectCards } from "../selectors";
import { isValidUploadIdParam } from "../rules";
import type { SetupFlowResult } from "../types";

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message.trim()) return error.message;
  return fallback;
}

function ensureApiSuccess<T>(response: ApiResponse<T>, fallback: string): T {
  if (!response.success || !response.data) {
    throw new Error(response.error?.message ?? fallback);
  }
  return response.data;
}

export function useSetupFlow(uploadIdParam: string): SetupFlowResult {
  const [upload, setUpload] = useState<UploadRecord | null>(null);
  const [externalConsentStatus, setExternalConsentStatus] = useState<ConsentStatusValue | null>(null);
  const [loading, setLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [uploadNotFound, setUploadNotFound] = useState(false);
  const [expandedProjectName, setExpandedProjectName] = useState<string | null>(null);

  const hasValidUploadId = useMemo(() => isValidUploadIdParam(uploadIdParam), [uploadIdParam]);
  const uploadId = hasValidUploadId ? Number.parseInt(uploadIdParam, 10) : null;
  const manualOnlySummaries = externalConsentStatus !== "accepted";

  const projectCards = useMemo(() => deriveProjectCards(upload), [upload]);
  const individualProjects = useMemo(
    () => projectCards.filter((project) => project.classification === "individual"),
    [projectCards],
  );
  const collaborativeProjects = useMemo(
    () => projectCards.filter((project) => project.classification === "collaborative"),
    [projectCards],
  );

  const loadUpload = useCallback(async (targetUploadId: number, mode: "initial" | "refresh" = "initial") => {
    if (mode === "initial") setLoading(true);
    else setIsRefreshing(true);

    setLoadError(null);

    try {
      const res = await getUploadStatus(targetUploadId);
      const data = ensureApiSuccess(res, "Failed to load setup context.");
      setUpload(data);
      setUploadNotFound(false);
      return true;
    } catch (error: unknown) {
      const message = getErrorMessage(error, "Failed to load setup context.");
      setLoadError(message);
      setUpload(null);

      if (message.toLowerCase().includes("upload not found")) {
        setUploadNotFound(true);
      }
      return false;
    } finally {
      if (mode === "initial") setLoading(false);
      else setIsRefreshing(false);
    }
  }, []);

  const refreshUpload = useCallback(async () => {
    if (uploadId === null) return false;
    return loadUpload(uploadId, "refresh");
  }, [loadUpload, uploadId]);

  useEffect(() => {
    if (uploadId === null) return;
    const targetUploadId = uploadId;

    let active = true;

    async function runInitialLoad() {
      const ok = await loadUpload(targetUploadId, "initial");
      if (!active) return;
      if (!ok) return;
    }

    runInitialLoad();
    return () => {
      active = false;
    };
  }, [loadUpload, uploadId]);

  useEffect(() => {
    let active = true;

    async function loadConsentStatus() {
      try {
        const res = await getConsentStatus();
        if (!active) return;
        setExternalConsentStatus(res.data?.external_consent ?? null);
      } catch {
        if (!active) return;
        setExternalConsentStatus(null);
      }
    }

    loadConsentStatus();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (projectCards.length === 0) {
      setExpandedProjectName(null);
      return;
    }
    if (expandedProjectName && projectCards.some((project) => project.projectName === expandedProjectName)) return;
    setExpandedProjectName(projectCards[0].projectName);
  }, [expandedProjectName, projectCards]);

  const clearActionError = useCallback(() => {
    setActionError(null);
  }, []);

  const ensureUploadId = useCallback(() => {
    if (uploadId !== null) return uploadId;
    setActionError("Missing upload context. Please return to step 2 and continue again.");
    return null;
  }, [uploadId]);

  const runUploadMutation = useCallback(
    async (runner: () => Promise<ApiResponse<UploadRecord>>, fallback: string) => {
      setActionError(null);
      setIsMutating(true);

      try {
        const res = await runner();
        const data = ensureApiSuccess(res, fallback);
        setUpload(data);
        setUploadNotFound(false);
        return data;
      } catch (error: unknown) {
        setActionError(getErrorMessage(error, fallback));
        return null;
      } finally {
        setIsMutating(false);
      }
    },
    [],
  );

  const runDataRequest = useCallback(
    async <T,>(
      runner: () => Promise<ApiResponse<T>>,
      fallback: string,
      refreshAfter = false,
    ): Promise<T | null> => {
      setActionError(null);
      setIsMutating(true);

      try {
        const res = await runner();
        const data = ensureApiSuccess(res, fallback);
        if (refreshAfter) {
          await refreshUpload();
        }
        return data;
      } catch (error: unknown) {
        setActionError(getErrorMessage(error, fallback));
        return null;
      } finally {
        setIsMutating(false);
      }
    },
    [refreshUpload],
  );

  function onToggleProject(projectName: string) {
    setExpandedProjectName((prev) => (prev === projectName ? null : projectName));
  }

  const actions = useMemo(
    () => ({
      getProjectFiles: async (projectKey: number) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runDataRequest(
          () => getUploadProjectFiles(id, projectKey),
          "Failed to load project files.",
        );
      },
      setMainFile: async (projectKey: number, relpath: string) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runUploadMutation(
          () => postUploadProjectMainFile(id, projectKey, relpath),
          "Failed to save selected main file.",
        );
      },
      getMainFileSections: async (projectKey: number) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runDataRequest(
          () => getUploadProjectTextSections(id, projectKey),
          "Failed to load main file sections.",
        );
      },
      setContributedSections: async (projectKey: number, selectedSectionIds: number[]) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runUploadMutation(
          () => postUploadProjectTextContributions(id, projectKey, selectedSectionIds),
          "Failed to save contributed sections.",
        );
      },
      setSupportingTextFiles: async (projectKey: number, relpaths: string[]) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runUploadMutation(
          () => postUploadProjectSupportingTextFiles(id, projectKey, relpaths),
          "Failed to save supporting text files.",
        );
      },
      setSupportingCsvFiles: async (projectKey: number, relpaths: string[]) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runUploadMutation(
          () => postUploadProjectSupportingCsvFiles(id, projectKey, relpaths),
          "Failed to save supporting CSV files.",
        );
      },
      setKeyRole: async (projectKey: number, keyRole: string) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runUploadMutation(
          () => postUploadProjectKeyRole(id, projectKey, keyRole),
          "Failed to save key role.",
        );
      },
      getGitIdentities: async (projectKey: number) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runDataRequest(
          () => getUploadProjectGitIdentities(id, projectKey),
          "Failed to load git identities.",
        );
      },
      saveGitIdentities: async (projectKey: number, selectedIndices: number[], extraEmails: string[] = []) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runDataRequest(
          () => postUploadProjectGitIdentities(id, projectKey, selectedIndices, extraEmails),
          "Failed to save git identity selections.",
          true,
        );
      },
      saveManualProjectSummary: async (projectKey: number, summaryText: string) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runUploadMutation(
          () => postUploadProjectManualProjectSummary(id, projectKey, summaryText),
          "Failed to save manual project summary.",
        );
      },
      saveManualContributionSummary: async (projectKey: number, contributionSummary: string) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runUploadMutation(
          () => postUploadProjectManualContributionSummary(id, projectKey, contributionSummary),
          "Failed to save manual contribution summary.",
        );
      },
      checkRunReadiness: async (scope: RunScope = "all") => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runDataRequest(
          () => postUploadRun(id, { scope, force_rerun: false, mode: "check" }),
          "Failed to check analysis readiness.",
        );
      },
      githubStart: async (projectName: string, connectNow: boolean) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runDataRequest(
          () => postUploadProjectGithubStart(id, projectName, connectNow),
          "Failed to update GitHub connection state.",
          true,
        );
      },
      githubRepos: async (projectName: string) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runDataRequest(
          () => getUploadProjectGithubRepos(id, projectName),
          "Failed to load GitHub repositories.",
        );
      },
      githubLink: async (projectName: string, repoFullName: string) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runDataRequest(
          () => postUploadProjectGithubLink(id, projectName, repoFullName),
          "Failed to link GitHub repository.",
          true,
        );
      },
      driveStart: async (projectName: string, connectNow: boolean) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runDataRequest(
          () => postUploadProjectDriveStart(id, projectName, connectNow),
          "Failed to update Google Drive connection state.",
          true,
        );
      },
      driveFiles: async (projectName: string) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runDataRequest(
          () => getUploadProjectDriveFiles(id, projectName),
          "Failed to load Google Drive files.",
        );
      },
      driveLink: async (projectName: string, links: DriveLinkItemRequest[]) => {
        const id = ensureUploadId();
        if (id === null) return null;
        return runDataRequest(
          () => postUploadProjectDriveLink(id, projectName, links),
          "Failed to link Google Drive files.",
          true,
        );
      },
    }),
    [ensureUploadId, runDataRequest, runUploadMutation],
  );

  return {
    upload,
    hasValidUploadId,
    uploadId,
    uploadStatus: upload?.status ?? null,
    externalConsentStatus,
    manualOnlySummaries,
    loading,
    isRefreshing,
    isMutating,
    loadError,
    actionError,
    uploadNotFound,
    projectCards,
    individualProjects,
    collaborativeProjects,
    expandedProjectName,
    onToggleProject,
    clearActionError,
    refreshUpload,
    actions,
  };
}
