import { useEffect, useState } from "react";
import type { UploadStatus } from "../../../../../api/uploads";
import type { SetupFlowResult, SetupProjectCard } from "../../types";

type Props = {
  project: SetupProjectCard;
  actions: SetupFlowResult["actions"];
  isMutating: boolean;
  uploadStatus: UploadStatus | null;
  manualOnlySummaries: boolean;
};

function canSaveSummaryInStatus(uploadStatus: UploadStatus | null): boolean {
  return uploadStatus === "needs_summaries" || uploadStatus === "analyzing" || uploadStatus === "done";
}

export default function ManualSummarySection({
  project,
  actions,
  isMutating,
  uploadStatus,
  manualOnlySummaries,
}: Props) {
  const [summaryText, setSummaryText] = useState(project.manualProjectSummary);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    setSummaryText(project.manualProjectSummary);
  }, [project.manualProjectSummary]);

  const canSave = canSaveSummaryInStatus(uploadStatus);

  async function onSave() {
    setSaveMessage(null);
    if (project.projectKey === null) return;
    const data = await actions.saveManualProjectSummary(project.projectKey, summaryText);
    if (!data) return;
    setSaveMessage("Manual project summary saved.");
  }

  return (
    <div className="rounded-lg border border-zinc-200 bg-white px-3 py-2">
      <h4 className="mb-1 text-sm leading-tight font-semibold text-zinc-900">Project Summary</h4>
      {manualOnlySummaries && (
        <p className="mb-2 rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800">
          No external LLM consent granted. Manual summary is required.
        </p>
      )}
      <textarea
        value={summaryText}
        onChange={(event) => setSummaryText(event.target.value)}
        placeholder="Input your project summary here"
        className="min-h-[82px] w-full rounded border border-zinc-300 bg-white px-2 py-2 text-xs"
        disabled={isMutating}
      />
      <div className="mt-2 flex items-center gap-2">
        <button
          type="button"
          onClick={onSave}
          disabled={isMutating || !canSave || project.projectKey === null}
          className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
        >
          Save project summary
        </button>
        {!canSave && (
          <span className="text-xs text-zinc-600">
            Available after setup reaches summaries stage.
          </span>
        )}
      </div>
      {saveMessage && <p className="mt-1 text-xs text-zinc-700">{saveMessage}</p>}
    </div>
  );
}
