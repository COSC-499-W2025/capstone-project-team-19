import { getUsername } from "../auth/user";
import UploadWizardShell from "../components/UploadWizardShell";
import "./Upload.css";

export default function UploadSetupPage() {
  const username = getUsername();

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "inactive" as const, to: "/upload/upload" },
    { label: "3. Setup", status: "active" as const },
  ];

  return (
    <UploadWizardShell username={username} steps={steps} actionLabel="Next" actionDisabled showAction>
      <div className="wizardPlaceholderCard">
        <p className="wizardPlaceholderText">Setup placeholder.</p>
      </div>
    </UploadWizardShell>
  );
}
