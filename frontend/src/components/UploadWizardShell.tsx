import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import TopBar from "./TopBar";
import { PageContainer, PageHeader, SectionCard } from "./shared";

type StepStatus = "active" | "inactive" | "disabled";

export type WizardStep = {
  label: string;
  status: StepStatus;
  to?: string;
  onClick?: () => void;
  disabled?: boolean;
};

type Props = {
  username: string;
  steps: WizardStep[];
  actionLabel: string;
  children: ReactNode;
  onAction?: () => void;
  actionDisabled?: boolean;
  showAction?: boolean;
  breadcrumbs: { label: string; href?: string }[];
};

export default function UploadWizardShell({
  username,
  steps,
  actionLabel,
  children,
  onAction,
  actionDisabled = false,
  showAction = true,
  breadcrumbs,
}: Props) {
  const nav = useNavigate();

  return (
    <>
      <TopBar showNav username={username} />

      <div className="wizardPage">
        <PageContainer className="pt-[12px]">
          <PageHeader breadcrumbs={breadcrumbs} />

          <SectionCard className="w-full max-w-[1110px] self-center overflow-hidden !p-0 bg-white">
            <div className="wizardLayout">
              <aside className="wizardSidebar">
                <div className="wizardSidebarSticky">
                  <div className="wizardProgressTitle">Progress</div>

                  <div className="wizardSteps">
                    {steps.map((step) => {
                      const stepDisabled =
                        step.disabled ?? step.status === "disabled";
                      const stepClickable =
                        !stepDisabled &&
                        (Boolean(step.to) || Boolean(step.onClick));

                      return (
                        <button
                          key={step.label}
                          type="button"
                          className={`wizardStep wizardStep--${step.status}${
                            stepClickable ? " wizardStep--clickable" : ""
                          }`}
                          disabled={stepDisabled}
                          aria-disabled={stepDisabled}
                          onClick={() => {
                            if (stepDisabled) return;
                            if (step.onClick) {
                              step.onClick();
                              return;
                            }
                            if (step.to) nav(step.to);
                          }}
                        >
                          {step.label}
                        </button>
                      );
                    })}
                  </div>

                  {showAction && (
                    <button
                      type="button"
                      className="wizardActionBtn"
                      onClick={onAction}
                      disabled={actionDisabled}
                    >
                      {actionLabel}
                    </button>
                  )}
                </div>
              </aside>

              <div className="wizardDivider" aria-hidden="true" />

              <main className="wizardContent">{children}</main>
            </div>
          </SectionCard>
        </PageContainer>
      </div>
    </>
  );
}