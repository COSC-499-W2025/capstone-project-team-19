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
      <div className="max-w-[1040px] space-y-8 rounded-xl bg-[var(--upload-bg)] p-6 max-[980px]:p-4">
        <header>
          <h2 className="text-4xl leading-tight font-semibold text-zinc-900">Analyzing files....</h2>
        </header>

        <section className="space-y-6">
          <div className="rounded-2xl border border-zinc-300 bg-zinc-50 p-4">
            <p className="text-lg font-semibold text-zinc-900">Analyzing individual projects</p>
            <p className="mb-3 text-sm text-zinc-600">Completed.</p>
            <div className="h-2 w-full rounded bg-zinc-200">
              <div className="h-2 w-full rounded bg-black" />
            </div>
          </div>

          <div className="rounded-2xl border border-zinc-300 bg-zinc-50 p-4">
            <div className="mb-2 flex items-center justify-between gap-3">
              <p className="text-lg font-semibold text-zinc-900">Analyzing collaborative projects</p>
              <p className="text-sm text-zinc-600">In progress</p>
            </div>
            <p className="mb-3 text-sm text-zinc-600">65% • 30 seconds remaining</p>
            <div className="h-2 w-full rounded bg-zinc-200">
              <div className="h-2 w-[65%] rounded bg-black" />
            </div>
          </div>
        </section>

        <p className="mx-auto max-w-[850px] pt-8 text-center text-3xl leading-snug text-zinc-900 max-[980px]:text-base">
          All analysis is complete. You can view, manage, and customize results in the Projects or Insights tabs.
          You can also export them as a resume or portfolio from the Outputs tab.
        </p>
      </div>
    </UploadWizardShell>
  );
}
