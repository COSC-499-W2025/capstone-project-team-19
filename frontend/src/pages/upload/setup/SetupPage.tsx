import { useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getUsername } from "../../../auth/user";
import UploadWizardShell from "../../../components/UploadWizardShell";
import "../UploadShared.css";

export default function UploadSetupPage() {
  const username = getUsername();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();

  const uploadIdParam = searchParams.get("uploadId") ?? "";
  const hasValidUploadId = useMemo(() => /^[1-9]\d*$/.test(uploadIdParam), [uploadIdParam]);

  useEffect(() => {
    if (hasValidUploadId) return;
    nav("/upload/upload", { replace: true });
  }, [hasValidUploadId, nav]);

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "inactive" as const, to: "/upload/upload" },
    { label: "3. Setup", status: "active" as const },
  ];

  if (!hasValidUploadId) return null;

  return (
    <UploadWizardShell username={username} steps={steps} actionLabel="Next" actionDisabled showAction>
      <div className="wizardPlaceholderCard">
        <p className="wizardPlaceholderText">Setup placeholder for upload {uploadIdParam}.</p>
      </div>
    </UploadWizardShell>
  );
}
