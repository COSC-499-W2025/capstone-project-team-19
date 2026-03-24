import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getUsername } from "../../../auth/user";
import UploadWizardShell from "../../../components/UploadWizardShell";
import { getConsentStatus, postExternalConsent, postInternalConsent } from "../../../api/consent";
import type { ConsentStatusValue } from "../../../api/consent";

export default function ConsentPage() {
  const username = getUsername();
  const nav = useNavigate();
  const [internalConsent, setInternalConsent] = useState<ConsentStatusValue | null>(null);
  const [externalConsent, setExternalConsent] = useState<ConsentStatusValue | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadStatus() {
      setLoadingStatus(true);
      setStatusError(null);
      try {
        const res = await getConsentStatus();
        if (!active) return;
        setInternalConsent(res.data?.internal_consent ?? null);
        setExternalConsent(res.data?.external_consent ?? null);
      } catch (e: unknown) {
        if (!active) return;
        setStatusError(e instanceof Error ? e.message : "Failed to load consent status.");
      } finally {
        if (active) setLoadingStatus(false);
      }
    }

    loadStatus();
    return () => {
      active = false;
    };
  }, []);

  async function onNext() {
    setSubmitError(null);

    if (internalConsent !== "accepted") {
      setSubmitError("Please select \"Yes, I consent.\" for user consent to continue.");
      return;
    }
    if (!externalConsent) {
      setSubmitError("Please select an external service consent option to continue.");
      return;
    }

    setSubmitting(true);
    try {
      const internalRes = await postInternalConsent(internalConsent);
      if (!internalRes.success) {
        throw new Error(internalRes.error?.message ?? "Failed to save internal consent.");
      }

      const externalRes = await postExternalConsent(externalConsent);
      if (!externalRes.success) {
        throw new Error(externalRes.error?.message ?? "Failed to save external consent.");
      }

      nav("/upload/upload");
    } catch (e: unknown) {
      setSubmitError(e instanceof Error ? e.message : "Failed to save consent choices.");
    } finally {
      setSubmitting(false);
    }
  }

  const controlsDisabled = loadingStatus || submitting;
  const steps = [
    { label: "1. Consent", status: "active" as const },
    { label: "2. Upload", status: "inactive" as const, onClick: onNext, disabled: controlsDisabled },
    { label: "3. Setup", status: "disabled" as const, disabled: true },
    { label: "4. Analyze", status: "disabled" as const, disabled: true },
  ];

  return (
    <UploadWizardShell
      username={username}
      steps={steps}
      actionLabel={submitting ? "Saving..." : "Next"}
      onAction={onNext}
      actionDisabled={controlsDisabled}
      breadcrumbs={[
        { label: "Home", href: "/" },
        { label: "Upload", href: "/upload" },
        { label: "Consent", href: "/upload/consent" },
      ]}
    >
      <div className="consentContent">
        {loadingStatus && <p className="consentStatusLine">Loading saved consent status...</p>}
        {statusError && (
          <p className="error consentStatusLine" style={{ whiteSpace: "pre-line" }}>
            {statusError}
          </p>
        )}
        {submitError && (
          <p className="error consentStatusLine" style={{ whiteSpace: "pre-line" }}>
            {submitError}
          </p>
        )}

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
            <input
              className="consentChoiceRadio"
              type="radio"
              name="internal-consent"
              value="accepted"
              checked={internalConsent === "accepted"}
              disabled={controlsDisabled}
              onChange={() => setInternalConsent("accepted")}
            />
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
            <input
              className="consentChoiceRadio"
              type="radio"
              name="external-consent"
              value="accepted"
              checked={externalConsent === "accepted"}
              disabled={controlsDisabled}
              onChange={() => setExternalConsent("accepted")}
            />
            <span>Yes, I consent.</span>
          </label>

          <label className="consentChoice">
            <input
              className="consentChoiceRadio"
              type="radio"
              name="external-consent"
              value="rejected"
              checked={externalConsent === "rejected"}
              disabled={controlsDisabled}
              onChange={() => setExternalConsent("rejected")}
            />
            <span>No, I don&apos;t want to use LLM.</span>
          </label>
        </section>
      </div>
    </UploadWizardShell>
  );
}
