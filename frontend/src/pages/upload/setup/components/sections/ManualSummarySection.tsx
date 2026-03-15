import { useEffect, useState } from "react";
import type { SetupFlowResult, SetupProjectCard, SummaryMode } from "../../types";

type Props = {
  project: SetupProjectCard;
  actions: SetupFlowResult["actions"];
  isMutating: boolean;
  manualOnlySummaries: boolean;
  mode: SummaryMode;
  onModeChange: (mode: SummaryMode) => void;
};

export default function ManualSummarySection({
  project,
  actions,
  isMutating,
  manualOnlySummaries,
  mode,
  onModeChange,
}: Props) {
  const [summaryText, setSummaryText] = useState(project.manualProjectSummary);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    setSummaryText(project.manualProjectSummary);
  }, [project.manualProjectSummary]);

  async function onSave() {
    setSaveMessage(null);
    if (project.projectKey === null) return;
    if (mode !== "manual") return;
    const data = await actions.saveManualProjectSummary(project.projectKey, summaryText);
    if (!data) return;
    setSaveMessage("Manual project summary saved.");
  }

  return (
    <div className="space-y-2">
      <h4 className="text-lg leading-tight font-semibold text-zinc-900">Project Summary</h4>
      <div className="space-y-1 text-sm text-zinc-800">
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name={`project-summary-mode-${project.projectName}`}
            checked={mode === "llm"}
            onChange={() => onModeChange("llm")}
            disabled={isMutating || manualOnlySummaries}
          />
          <span>Use LLM summary</span>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name={`project-summary-mode-${project.projectName}`}
            checked={mode === "manual"}
            onChange={() => onModeChange("manual")}
            disabled={isMutating}
          />
          <span>Input manual summary</span>
        </label>
      </div>
      {manualOnlySummaries && (
        <p className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          No external LLM consent granted. Manual summary is required.
        </p>
      )}
      {mode === "manual" ? (
        <>
          <textarea
            value={summaryText}
            onChange={(event) => setSummaryText(event.target.value)}
            placeholder="Input your project summary here"
            className="min-h-[120px] w-full rounded border border-zinc-300 bg-zinc-50 px-3 py-2 text-sm"
            disabled={isMutating}
          />
          <div className="mt-2 flex items-center gap-2">
            <button
              type="button"
              onClick={onSave}
              disabled={isMutating || project.projectKey === null}
              className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
            >
              Save project summary
            </button>
          </div>
        </>
      ) : (
        mode === "llm" && (
          <p className="text-sm text-zinc-600">Summary will be generated with LLM during analysis.</p>
        )
      )}
      {saveMessage && <p className="mt-1 text-sm text-zinc-700">{saveMessage}</p>}
    </div>
  );
}
