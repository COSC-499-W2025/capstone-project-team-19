import { useEffect, useState } from "react";
import type { SetupFlowResult, SetupProjectCard } from "../../types";
import { setupPrimaryActionButtonClass } from "./buttonStyles";

type Props = {
  project: SetupProjectCard;
  actions: SetupFlowResult["actions"];
  isMutating: boolean;
};

export default function KeyRoleSection({ project, actions, isMutating }: Props) {
  const [keyRole, setKeyRole] = useState(project.keyRole);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    setKeyRole(project.keyRole);
  }, [project.keyRole]);

  async function onSave() {
    setSaveMessage(null);
    if (project.projectKey === null) return;
    const data = await actions.setKeyRole(project.projectKey, keyRole);
    if (!data) return;
    setSaveMessage("Key role saved.");
  }

  return (
    <div className="space-y-2">
      <h4 className="text-lg leading-tight font-semibold text-zinc-900">Key Role</h4>
      <input
        type="text"
        value={keyRole}
        onChange={(event) => setKeyRole(event.target.value)}
        placeholder="e.g., Backend Developer, Research Assistant"
        className="h-12 w-full rounded !border !border-zinc-300 !bg-zinc-50 !px-4 !py-3 text-sm text-zinc-700 placeholder:text-zinc-400 disabled:!border-zinc-300 disabled:!bg-zinc-50"
        disabled={isMutating}
      />
      <div className="mt-2 flex items-center gap-2">
        <button
          type="button"
          onClick={onSave}
          disabled={isMutating || project.projectKey === null}
          className={setupPrimaryActionButtonClass}
        >
          Save key role
        </button>
        <span className="text-sm text-zinc-600">
          Leave blank to clear. If LLM consent is enabled, this can be auto-generated during analysis.
        </span>
      </div>
      {saveMessage && <p className="mt-1 text-sm text-zinc-700">{saveMessage}</p>}
    </div>
  );
}
