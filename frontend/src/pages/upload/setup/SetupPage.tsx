import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getUsername } from "../../../auth/user";
import UploadWizardShell from "../../../components/UploadWizardShell";
import "../UploadShared.css";
import SetupProjectGroup from "./components/SetupProjectGroup";
import { useSetupFlow } from "./hooks/useSetupFlow";

export default function UploadSetupPage() {
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

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "inactive" as const, to: "/upload/upload" },
    { label: "3. Setup", status: "active" as const },
  ];

  if (!flow.hasValidUploadId) return null;

  return (
    <UploadWizardShell username={username} steps={steps} actionLabel="Next" actionDisabled showAction>
      <div className="max-w-[1040px] rounded-xl bg-[var(--upload-bg)] p-6 max-[980px]:p-4">
        <header className="mb-4">
          <h2 className="wizardPlaceholderTitle">Setup</h2>
          <p className="wizardPlaceholderText">
            Review project setup details before analysis. Upload #{uploadIdParam}
          </p>
        </header>

        {flow.loading && <p className="mb-3 text-sm">Loading project setup context...</p>}
        {flow.loadError && <p className="error mb-3 text-sm">{flow.loadError}</p>}
        {!flow.loading && !flow.loadError && flow.projectCards.length === 0 && (
          <p className="mb-3 text-sm">No projects found for this upload.</p>
        )}

        {!flow.loading && !flow.loadError && flow.projectCards.length > 0 && (
          <div className="space-y-6">
            <SetupProjectGroup
              title="Individual Projects"
              projects={flow.individualProjects}
              emptyLabel="No individual projects."
              expandedProjectName={flow.expandedProjectName}
              onToggleProject={flow.onToggleProject}
            />

            <SetupProjectGroup
              title="Collaborative Projects"
              projects={flow.collaborativeProjects}
              emptyLabel="No collaborative projects."
              expandedProjectName={flow.expandedProjectName}
              onToggleProject={flow.onToggleProject}
            />
          </div>
        )}
      </div>
    </UploadWizardShell>
  );
}
