import { useNavigate } from "react-router-dom";
import { getUsername } from "../auth/user";
import UploadWizardShell from "../components/UploadWizardShell";

export default function ConsentPage() {
  const username = getUsername();
  const nav = useNavigate();

  const steps = [
    { label: "1. Consent", status: "active" as const },
    { label: "2. Upload", status: "disabled" as const },
    { label: "3. Setup", status: "disabled" as const },
  ];

  return (
    <UploadWizardShell
      username={username}
      steps={steps}
      actionLabel="Next"
      onAction={() => nav("/upload/upload")}
    >
      <div className="consentContent">
        <section className="consentSectionBlock">
          <h2 className="consentSectionTitle">USER CONSENT NOTICE</h2>

          <p>
            This application analyzes your local digital work artifacts (e.g. documents, code repositories, notes,
            or media files) to help you gain insights about your work contributions, creative processes, and project
            evolution. The goal is to help you reflect on your productivity and showcase your professional growth.
          </p>

          <p>Before continuing, please read the following terms:</p>

          <ul className="consentBulletList">
            <li>All data processing occurs locally on your machine.</li>
            <li>No files or personal information are uploaded, shared, or transmitted.</li>
            <li>You may withdraw consent at any time by deleting your consent record or uninstalling the application.</li>
            <li>The system will access only directories or files that you explicitly select.</li>
            <li>Your consent status (Accepted or Rejected) and timestamp will be stored locally in a small SQLite database on your machine.</li>
          </ul>

          <p>
            By selecting &quot;Yes, I consent.&quot;, you give your consent for the application to analyze your selected local files according to the description above.
          </p>

          <label className="consentChoice">
            <input className="consentChoiceRadio" type="radio" name="internal-consent" value="accepted" />
            <span>Yes, I consent.</span>
          </label>
        </section>

        <section className="consentSectionBlock">
          <h2 className="consentSectionTitle">EXTERNAL SERVICE CONSENT NOTICE</h2>

          <p>
            This application may send some of your data to external services (e.g. LLM) to analyze your digital work artifacts.
          </p>

          <p>Before continuing, please read the following terms:</p>

          <ul className="consentBulletList">
            <li>Using external services may send your files or content off your device.</li>
            <li>We have no control over what external services do with your data. They may store, process, or use it according to their own policies.</li>
            <li>You may withdraw consent at any time, which will prevent future external analyses.</li>
            <li>Data already sent to external services cannot be recalled or deleted by this system.</li>
            <li>Declining consent will not prevent you from using the system locally. Local analysis will still work with all basic features, but may not be as accurate as the using of external service.</li>
          </ul>

          <p>
            By selecting &quot;Yes, I consent.&quot;, you give your consent for the application to analyze your selected local files using LLM.
          </p>

          <label className="consentChoice">
            <input className="consentChoiceRadio" type="radio" name="external-consent" value="accepted" />
            <span>Yes, I consent.</span>
          </label>

          <label className="consentChoice">
            <input className="consentChoiceRadio" type="radio" name="external-consent" value="rejected" />
            <span>No, I don&apos;t want to use LLM.</span>
          </label>
        </section>
      </div>
    </UploadWizardShell>
  );
}
