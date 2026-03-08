import { getUsername } from "../auth/user";
import UploadWizardShell from "../components/UploadWizardShell";

export default function UploadPage() {
  const username = getUsername();
  const steps = [
    { label: "1. Consent", status: "disabled" as const },
    { label: "2. Upload", status: "active" as const },
    { label: "3. Setup", status: "disabled" as const },
  ];

  return (
    <UploadWizardShell username={username} steps={steps} actionLabel="Next">
      <div className="wizardPlaceholderCard">
        <h2 className="wizardPlaceholderTitle">Upload Placeholder</h2>
        <p className="wizardPlaceholderText">This is the step 2 upload placeholder.</p>
        <div className="wizardPlaceholderNote">
          File upload controls and dedup/classification UI will be added next.
        </div>
      </div>
    </UploadWizardShell>
  );
}
