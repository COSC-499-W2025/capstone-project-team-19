import { getUsername } from "../auth/user";
import UploadWizardShell from "../components/UploadWizardShell";

export default function UploadPage() {
  const username = getUsername();
  const steps = [
    { label: "1. Consent", status: "inactive" as const },
    { label: "2. Upload", status: "active" as const },
    { label: "3. Setup", status: "disabled" as const },
  ];

  return (
    <UploadWizardShell username={username} steps={steps} actionLabel="Next">
      <div className="wizardPlaceholderCard">
        <h2 className="wizardPlaceholderTitle">Upload Placeholder</h2>
        <p className="wizardPlaceholderText">This is placeholder content for step 2 (Upload).</p>
        <div className="wizardPlaceholderNote">
          Left progress sidebar is implemented and sticky.
        </div>
      </div>
    </UploadWizardShell>
  );
}
