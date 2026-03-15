import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getUsername } from "../../../auth/user";
import UploadWizardShell from "../../../components/UploadWizardShell";
import "../UploadShared.css";
import { useSetupFlow } from "../setup/hooks/useSetupFlow";

export default function UploadAnalyzePage() {
  const username = getUsername();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();

  const uploadIdParam = searchParams.get("uploadId") ?? "";
  const flow = useSetupFlow(uploadIdParam);

  useEffect(() => {
    if (flow.hasValidUploadId) return;
    nav("/upload/upload", { replace: true });
  }, [flow.hasValidUploadId, nav]);

  useEffect(() => {
    if (!flow.uploadNotFound) return;
    nav("/upload/upload", { replace: true });
  }, [flow.uploadNotFound, nav]);

  if (!flow.hasValidUploadId) return null;

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "inactive" as const, to: "/upload/upload" },
    { label: "3. Setup", status: "disabled" as const, disabled: true },
    { label: "4. Analyze", status: "active" as const },
  ];

  const statusText =
    flow.uploadStatus === "analyzing"
      ? "Analysis is running. This page is a placeholder for live progress."
      : flow.uploadStatus === "done"
        ? "Analysis has completed. Detailed progress and controls are coming soon."
        : "Analysis has not started yet. Return to setup when your selections are ready.";

  return (
    <UploadWizardShell username={username} steps={steps} actionLabel="Analyze" showAction={false}>
      <div className="max-w-[1040px] rounded-xl bg-[var(--upload-bg)] p-6 max-[980px]:p-4">
        <header className="mb-4">
          <h2 className="wizardPlaceholderTitle">Analyze</h2>
          <p className="wizardPlaceholderText">Coming soon. Upload #{uploadIdParam}</p>
        </header>

        {flow.loading && <p className="mb-3 text-sm">Loading analysis status...</p>}
        {flow.loadError && <p className="error mb-3 text-sm">{flow.loadError}</p>}
        {!flow.loading && !flow.loadError && (
          <p className="mb-4 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-800">
            {statusText}
          </p>
        )}

        <p className="text-xs text-zinc-600">
          Setup changes are disabled after analysis starts.
        </p>
      </div>
    </UploadWizardShell>
  );
}
