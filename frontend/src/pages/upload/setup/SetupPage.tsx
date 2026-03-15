import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getUsername } from "../../../auth/user";
import UploadWizardShell from "../../../components/UploadWizardShell";
import "../UploadShared.css";
import "./SetupPage.css";
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
      <div className="setupStagePanel">
        <header className="setupStageHeader">
          <h2 className="wizardPlaceholderTitle">Setup</h2>
          <p className="wizardPlaceholderText">
            Review project setup details before analysis. Upload #{uploadIdParam}
          </p>
        </header>

        {flow.loading && <p className="setupStageStateLine">Loading project setup context...</p>}
        {flow.loadError && <p className="error setupStageStateLine">{flow.loadError}</p>}
        {!flow.loading && !flow.loadError && flow.projectCards.length === 0 && (
          <p className="setupStageStateLine">No projects found for this upload.</p>
        )}

        {!flow.loading && !flow.loadError && flow.projectCards.length > 0 && (
          <div className="setupSections">
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
