import type { ReactNode } from "react";
import TopBar from "./TopBar";

type StepStatus = "active" | "inactive" | "disabled";

export type WizardStep = {
  label: string;
  status: StepStatus;
};

type Props = {
  username: string;
  steps: WizardStep[];
  actionLabel: string;
  children: ReactNode;
  onAction?: () => void;
  actionDisabled?: boolean;
};

export default function UploadWizardShell({
  username,
  steps,
  actionLabel,
  children,
  onAction,
  actionDisabled = false,
}: Props) {
  return (
    <>
      <TopBar showNav username={username} />

      <div className="wizardPage">
        <div className="wizardLayout">
          <aside className="wizardSidebar">
            <div className="wizardSidebarSticky">
              <div className="wizardProgressTitle">Progress</div>

              <div className="wizardSteps">
                {steps.map((step) => (
                  <button
                    key={step.label}
                    type="button"
                    className={`wizardStep wizardStep--${step.status}`}
                    disabled
                  >
                    {step.label}
                  </button>
                ))}
              </div>

              <button type="button" className="wizardActionBtn" onClick={onAction} disabled={actionDisabled}>
                {actionLabel}
              </button>
            </div>
          </aside>

          <div className="wizardDivider" aria-hidden="true" />

          <main className="wizardContent">{children}</main>
        </div>
      </div>
    </>
  );
}
