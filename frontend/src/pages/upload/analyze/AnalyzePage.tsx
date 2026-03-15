import { getUsername } from "../../../auth/user";
import UploadWizardShell from "../../../components/UploadWizardShell";
import "../UploadShared.css";

export default function UploadAnalyzePage() {
  const username = getUsername();

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "inactive" as const, to: "/upload/upload" },
    { label: "3. Setup", status: "disabled" as const, disabled: true },
    { label: "4. Analyze", status: "active" as const },
  ];

  return (
    <UploadWizardShell username={username} steps={steps} actionLabel="Analyze" showAction={false}>
      <div className="max-w-[1040px] rounded-xl bg-[var(--upload-bg)] p-6 max-[980px]:p-4">
        <header className="mb-4">
          <h2 className="wizardPlaceholderTitle">Analyze</h2>
          <p className="wizardPlaceholderText">Coming soon.</p>
        </header>
      </div>
    </UploadWizardShell>
  );
}
