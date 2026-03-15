import { useEffect, useMemo, useState } from "react";
import { getUploadStatus, type UploadRecord } from "../../../../api/uploads";
import { deriveProjectCards } from "../selectors";
import { isValidUploadIdParam } from "../rules";
import type { SetupFlowResult } from "../types";

export function useSetupFlow(uploadIdParam: string): SetupFlowResult {
  const [upload, setUpload] = useState<UploadRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [uploadNotFound, setUploadNotFound] = useState(false);
  const [expandedProjectName, setExpandedProjectName] = useState<string | null>(null);

  const hasValidUploadId = useMemo(() => isValidUploadIdParam(uploadIdParam), [uploadIdParam]);
  const uploadId = hasValidUploadId ? Number.parseInt(uploadIdParam, 10) : null;

  const projectCards = useMemo(() => deriveProjectCards(upload), [upload]);
  const individualProjects = useMemo(
    () => projectCards.filter((project) => project.classification === "individual"),
    [projectCards],
  );
  const collaborativeProjects = useMemo(
    () => projectCards.filter((project) => project.classification === "collaborative"),
    [projectCards],
  );

  useEffect(() => {
    if (uploadId === null) return;
    const targetUploadId = uploadId;
    let active = true;

    async function loadUpload() {
      setLoading(true);
      setLoadError(null);
      setUploadNotFound(false);

      try {
        const res = await getUploadStatus(targetUploadId);
        if (!active) return;

        if (!res.success || !res.data) {
          throw new Error(res.error?.message ?? "Failed to load setup context.");
        }

        setUpload(res.data);
      } catch (error: unknown) {
        if (!active) return;

        const message = error instanceof Error ? error.message : "Failed to load setup context.";
        setLoadError(message);
        setUpload(null);

        if (message.toLowerCase().includes("upload not found")) {
          setUploadNotFound(true);
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadUpload();
    return () => {
      active = false;
    };
  }, [uploadId]);

  useEffect(() => {
    if (projectCards.length === 0) {
      setExpandedProjectName(null);
      return;
    }
    if (expandedProjectName && projectCards.some((project) => project.projectName === expandedProjectName)) return;
    setExpandedProjectName(projectCards[0].projectName);
  }, [expandedProjectName, projectCards]);

  function onToggleProject(projectName: string) {
    setExpandedProjectName((prev) => (prev === projectName ? null : projectName));
  }

  return {
    upload,
    hasValidUploadId,
    uploadId,
    loading,
    loadError,
    uploadNotFound,
    projectCards,
    individualProjects,
    collaborativeProjects,
    expandedProjectName,
    onToggleProject,
  };
}
