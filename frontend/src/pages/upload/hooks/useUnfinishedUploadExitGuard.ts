import { useEffect } from "react";
import { useBeforeUnload, useNavigate } from "react-router-dom";
import { deleteUpload } from "../../../api/uploads";
import { clearUploadRecoveryStage } from "../upload/recoveryStage";

type Params = {
  enabled: boolean;
  uploadId: number | null;
  message: string;
  onRequestConfirmLeave?: (confirmNavigation: () => Promise<void>) => void;
  onCleanupError?: (message: string) => void;
};

function isUploadWizardPath(pathname: string): boolean {
  return pathname === "/upload" || pathname.startsWith("/upload/");
}

export function useUnfinishedUploadExitGuard({
  enabled,
  uploadId,
  message,
  onRequestConfirmLeave,
  onCleanupError,
}: Params) {
  const navigate = useNavigate();

  useBeforeUnload((event) => {
    if (!enabled) return;
    event.preventDefault();
    event.returnValue = "";
  });

  useEffect(() => {
    if (!enabled) return;

    function onDocumentClick(event: MouseEvent) {
      if (event.defaultPrevented) return;
      if (event.button !== 0) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

      const target = event.target as Element | null;
      const link = target?.closest("a[href]") as HTMLAnchorElement | null;
      if (!link) return;

      let nextUrl: URL;
      try {
        nextUrl = new URL(link.href, window.location.origin);
      } catch {
        return;
      }

      if (nextUrl.origin !== window.location.origin) return;
      if (isUploadWizardPath(nextUrl.pathname)) return;

      const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`;
      const nextPath = `${nextUrl.pathname}${nextUrl.search}${nextUrl.hash}`;
      if (nextPath === currentPath) return;

      event.preventDefault();

      const confirmNavigation = async () => {
        try {
          if (uploadId) {
            const res = await deleteUpload(uploadId);
            if (!res.success) {
              throw new Error(res.error?.message ?? "Failed to delete unfinished upload.");
            }
            clearUploadRecoveryStage(uploadId);
          }
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : "Failed to delete unfinished upload.";
          onCleanupError?.(message);
          return;
        }
        navigate(nextPath);
      };

      if (onRequestConfirmLeave) {
        onRequestConfirmLeave(confirmNavigation);
        return;
      }

      const confirmed = window.confirm(message);
      if (!confirmed) return;
      void confirmNavigation();
    }

    document.addEventListener("click", onDocumentClick, true);
    return () => {
      document.removeEventListener("click", onDocumentClick, true);
    };
  }, [enabled, message, navigate, onCleanupError, onRequestConfirmLeave, uploadId]);
}
