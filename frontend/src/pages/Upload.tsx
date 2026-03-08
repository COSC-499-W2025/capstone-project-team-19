import { useMemo, useState } from "react";
import { getUsername } from "../auth/user";
import UploadWizardShell from "../components/UploadWizardShell";

type UploadFlowStage = "upload" | "projects" | "deduplication" | "classification";

type StageDef = {
  key: UploadFlowStage;
  label: string;
  title: string;
  description: string;
};

const STAGES: StageDef[] = [
  {
    key: "upload",
    label: "Upload",
    title: "Upload Placeholder",
    description: "Stage shell only: upload controls will be implemented next.",
  },
  {
    key: "projects",
    label: "Projects",
    title: "Projects Placeholder",
    description: "Projects list section will render here in the next step.",
  },
  {
    key: "deduplication",
    label: "Deduplication",
    title: "Deduplication Placeholder",
    description: "Deduplication cards will render here one-by-one in the next step.",
  },
  {
    key: "classification",
    label: "Classification",
    title: "Classification Placeholder",
    description: "Classification and type controls will render here in the next step.",
  },
];

export default function UploadPage() {
  const username = getUsername();
  const [stageIndex, setStageIndex] = useState(0);

  const currentStage = useMemo(() => STAGES[stageIndex], [stageIndex]);
  const canGoBack = stageIndex > 0;
  const canGoNext = stageIndex < STAGES.length - 1;

  function onNext() {
    if (!canGoNext) return;
    setStageIndex((prev) => prev + 1);
  }

  function onBack() {
    if (!canGoBack) return;
    setStageIndex((prev) => prev - 1);
  }

  const steps = [
    { label: "1. Consent", status: "inactive" as const, to: "/upload/consent" },
    { label: "2. Upload", status: "active" as const },
    { label: "3. Setup", status: "disabled" as const, disabled: true },
  ];

  return (
    <UploadWizardShell
      username={username}
      steps={steps}
      actionLabel="Next"
      onAction={onNext}
      actionDisabled={!canGoNext}
    >
      <div className="wizardPlaceholderCard">
        <div className="uploadStageTabs" role="tablist" aria-label="Upload flow stages">
          {STAGES.map((stage, idx) => {
            const active = idx === stageIndex;
            return (
              <button
                key={stage.key}
                type="button"
                role="tab"
                aria-selected={active}
                className={`uploadStageTab${active ? " uploadStageTab--active" : ""}`}
                onClick={() => setStageIndex(idx)}
              >
                {idx + 1}. {stage.label}
              </button>
            );
          })}
        </div>

        <h2 className="wizardPlaceholderTitle">{currentStage.title}</h2>
        <p className="wizardPlaceholderText">Current stage: {currentStage.label}</p>
        <div className="wizardPlaceholderNote">
          {currentStage.description}
        </div>

        <div className="uploadStageNavRow">
          <button type="button" className="uploadStageBackBtn" onClick={onBack} disabled={!canGoBack}>
            Back
          </button>
        </div>
      </div>
    </UploadWizardShell>
  );
}
