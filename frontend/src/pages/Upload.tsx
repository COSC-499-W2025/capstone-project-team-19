import { useLocation } from "react-router-dom";
import { getUsername } from "../auth/user";
import UploadWizardShell from "../components/UploadWizardShell";

export default function UploadPage() {
  const username = getUsername();
  const location = useLocation();
  const isUploadStep = location.pathname === "/upload/upload";

  const steps = isUploadStep
    ? [
        { label: "1. Consent", status: "inactive" as const },
        { label: "2. Upload", status: "active" as const },
        { label: "3. Setup", status: "disabled" as const },
      ]
    : [
        { label: "1. Consent", status: "active" as const },
        { label: "2. Upload", status: "disabled" as const },
        { label: "3. Setup", status: "disabled" as const },
      ];

  return (
    <UploadWizardShell username={username} steps={steps} actionLabel="Next">
      <div className="wizardPlaceholderCard">
        <h2 className="wizardPlaceholderTitle">{isUploadStep ? "Upload Placeholder" : "Consent Placeholder"}</h2>
        <p className="wizardPlaceholderText">
          This is placeholder content for the upload wizard.
        </p>
        <div className="wizardPlaceholderNote">
          Left progress sidebar is implemented and sticky.
        </div>
      </div>
    </UploadWizardShell>
  );
}
