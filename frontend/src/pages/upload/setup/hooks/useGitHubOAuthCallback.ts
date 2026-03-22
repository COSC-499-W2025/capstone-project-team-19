import { useEffect } from "react";

type Deps = {
  searchParams: URLSearchParams;
  setSearchParams: (
    updater: (prev: URLSearchParams) => Record<string, string>,
    opts?: { replace?: boolean },
  ) => void;
  hasValidUploadId: boolean;
  refreshUpload: () => Promise<boolean>;
  setActionError: (message: string | null) => void;
};

/**
 * Handles the GitHub OAuth redirect that lands on the setup page.
 *
 * Two paths:
 * 1. **Popup** – The page was opened by `window.open` during the Connect
 *    flow.  Post a message back to the opener tab and close this tab.
 * 2. **Direct** – The user navigated here directly (e.g. popup was blocked
 *    and they clicked the fallback link).  Refresh upload data in-place and
 *    strip the query params.
 *
 * Also listens for cross-tab messages from the popup path so the opener
 * tab can react without a full page reload.
 */
export function useGitHubOAuthCallback({
  searchParams,
  setSearchParams,
  hasValidUploadId,
  refreshUpload,
  setActionError,
}: Deps) {
  // Handle ?github=success|error from the redirect
  useEffect(() => {
    const status = searchParams.get("github");
    if (!status) return;

    if (status === "success") {
      if (window.opener) {
        window.opener.postMessage({ type: "github-auth-success" }, window.location.origin);
        window.close();
        return;
      }
      if (hasValidUploadId) void refreshUpload();
    } else if (status === "error") {
      if (window.opener) {
        const msg = searchParams.get("message") ?? "GitHub authorization failed.";
        window.opener.postMessage({ type: "github-auth-error", message: msg }, window.location.origin);
        window.close();
        return;
      }
      setActionError(searchParams.get("message") ?? "GitHub authorization failed.");
    }

    setSearchParams(
      (prev) => {
        const p = new URLSearchParams(prev);
        p.delete("github");
        p.delete("message");
        return Object.fromEntries(p.entries());
      },
      { replace: true },
    );
  }, [searchParams, hasValidUploadId, refreshUpload, setActionError, setSearchParams]);

  // Listen for postMessage from a popup tab
  useEffect(() => {
    function onMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === "github-auth-success") {
        void refreshUpload();
      } else if (event.data?.type === "github-auth-error") {
        setActionError(event.data.message ?? "GitHub authorization failed.");
      }
    }
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [refreshUpload, setActionError]);
}
