import type { DedupCase, DedupDecisionValue, VisibleDedupDecision } from "../uploadTypes";

type Props = {
  visibleDedupCases: DedupCase[];
  currentDedupCase: DedupCase | null;
  dedupCaseIndex: number;
  dedupDecisions: Record<string, DedupDecisionValue>;
  savedDedupChoices: [string, VisibleDedupDecision][];
  canGoToPreviousDedupCase: boolean;
  canGoToNextDedupCase: boolean;
  onDecisionChange: (projectName: string, value: VisibleDedupDecision) => void;
  onPreviousCase: () => void;
  onNextCase: () => void;
};

export default function DedupStage({
  visibleDedupCases,
  currentDedupCase,
  dedupCaseIndex,
  dedupDecisions,
  savedDedupChoices,
  canGoToPreviousDedupCase,
  canGoToNextDedupCase,
  onDecisionChange,
  onPreviousCase,
  onNextCase,
}: Props) {
  function dedupLabel(choice: VisibleDedupDecision): string {
    if (choice === "new_project") return "New project";
    return "New version";
  }

  return (
    <div className="dedupStagePanel">
      <h2 className="wizardPlaceholderTitle">Deduplication</h2>
      <p className="wizardPlaceholderText">Review similar projects one-by-one and choose how each should be treated.</p>

      {visibleDedupCases.length === 0 ? (
        savedDedupChoices.length === 0 ? (
          <div className="uploadEmptyState">No deduplication found.</div>
        ) : (
          <div className="dedupSavedPanel">
            <div className="dedupSavedTitle">Saved decisions</div>
            <ul className="dedupSavedList">
              {savedDedupChoices.map(([projectName, choice]) => (
                <li key={projectName} className="dedupSavedItem">
                  <strong>{projectName}</strong>: {dedupLabel(choice)}
                </li>
              ))}
            </ul>
          </div>
        )
      ) : (
        <>
          <div className="dedupStageCaseCount">
            Case {dedupCaseIndex + 1} of {visibleDedupCases.length}
          </div>

          {currentDedupCase && (
            <div className="dedupStageCard">
              <div className="dedupStageSummary">
                Project "{currentDedupCase.projectName}" looks related to "{currentDedupCase.existingProjectName}".
              </div>

              <div className="dedupStageBadges">
                {currentDedupCase.similarityLabel && <span className="dedupStageBadge">{currentDedupCase.similarityLabel}</span>}
                {currentDedupCase.pathLabel && <span className="dedupStageBadge">{currentDedupCase.pathLabel}</span>}
                {currentDedupCase.filesLabel && <span className="dedupStageBadge">{currentDedupCase.filesLabel}</span>}
              </div>

              <label className="dedupStageOption">
                <input
                  type="radio"
                  name={`dedup-${currentDedupCase.projectName}`}
                  value="new_project"
                  checked={dedupDecisions[currentDedupCase.projectName] === "new_project"}
                  onChange={() => onDecisionChange(currentDedupCase.projectName, "new_project")}
                />
                <span>New project (separate, no merge history created)</span>
              </label>

              <label className="dedupStageOption">
                <input
                  type="radio"
                  name={`dedup-${currentDedupCase.projectName}`}
                  value="new_version"
                  checked={dedupDecisions[currentDedupCase.projectName] === "new_version"}
                  onChange={() => onDecisionChange(currentDedupCase.projectName, "new_version")}
                />
                <span>New version (links to existing history)</span>
              </label>
            </div>
          )}

          {savedDedupChoices.length > 0 && (
            <div className="dedupSavedPanel">
              <div className="dedupSavedTitle">Saved decisions</div>
              <ul className="dedupSavedList">
                {savedDedupChoices.map(([projectName, choice]) => (
                  <li key={projectName} className="dedupSavedItem">
                    <strong>{projectName}</strong>: {dedupLabel(choice)}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="dedupStagePager">
            <button type="button" className="dedupStagePagerBtn" onClick={onPreviousCase} disabled={!canGoToPreviousDedupCase}>
              Previous case
            </button>
            <button type="button" className="dedupStagePagerBtn" onClick={onNextCase} disabled={!canGoToNextDedupCase}>
              Next case
            </button>
          </div>
        </>
      )}
    </div>
  );
}
