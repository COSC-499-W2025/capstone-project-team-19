import { useEffect, useState } from "react";
import type { SetupFlowResult, SetupProjectCard } from "../../types";

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
    <div className="rounded-lg border border-zinc-200 bg-white px-3 py-2">
      <h4 className="mb-1 text-sm leading-tight font-semibold text-zinc-900">Key Role</h4>
      <p className="mb-2 text-xs leading-relaxed text-zinc-700">
        Describe your main role in this project (for example: Backend Developer, Research Assistant).
      </p>
      <input
        type="text"
        value={keyRole}
        onChange={(event) => setKeyRole(event.target.value)}
        placeholder="Input key role here"
        className="h-8 w-full rounded border border-zinc-300 bg-white px-2 text-xs"
        disabled={isMutating}
      />
      <div className="mt-2 flex items-center gap-2">
        <button
          type="button"
          onClick={onSave}
          disabled={isMutating || project.projectKey === null}
          className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
        >
          Save key role
        </button>
        <span className="text-xs text-zinc-600">Leave blank to clear.</span>
      </div>
      {saveMessage && <p className="mt-1 text-xs text-zinc-700">{saveMessage}</p>}
    </div>
  );
}
