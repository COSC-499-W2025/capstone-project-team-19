import { useEffect, useState } from "react";
import type { SetupFlowResult, SetupProjectCard } from "../../types";
import { setupPrimaryActionButtonClass } from "./buttonStyles";

const CODE_ROLES = [
  "Backend Developer",
  "Frontend Developer",
  "Full-Stack Developer",
  "Software Architect",
  "QA / Test Engineer",
  "Security Engineer",
  "Algorithms Engineer",
  "DevOps Engineer",
  "Data Engineer",
  "Software Developer",
];

const TEXT_ROLES = [
  "Lead Author",
  "Technical Writer",
  "Research Analyst",
  "Researcher",
  "Academic Writer",
  "Data Analyst",
  "Content Strategist",
  "Editor",
];

type Props = {
  project: SetupProjectCard;
  actions: SetupFlowResult["actions"];
  isMutating: boolean;
  manualOnlySummaries: boolean;
};

export default function KeyRoleSection({
  project,
  actions,
  isMutating,
  manualOnlySummaries,
}: Props) {
  const [selectedRole, setSelectedRole] = useState(project.keyRole || "");
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    setSelectedRole(project.keyRole || "");
  }, [project.keyRole]);

  if (!manualOnlySummaries) {
    return (
      <div className="space-y-2">
        <h4 className="text-lg leading-tight font-semibold text-zinc-900">Key Role</h4>
        <p className="text-sm text-zinc-500">
          Key role will be automatically generated during analysis based on your contribution summary.
        </p>
      </div>
    );
  }

  const roles = project.projectType === "code" ? CODE_ROLES : TEXT_ROLES;

  async function onSave() {
    setSaveMessage(null);
    if (project.projectKey === null) return;
    const data = await actions.setKeyRole(project.projectKey, selectedRole);
    if (!data) return;
    setSaveMessage("Key role saved.");
  }

  return (
    <div className="space-y-2">
      <h4 className="text-lg leading-tight font-semibold text-zinc-900">Key Role</h4>
      <p className="text-sm text-zinc-500">
        Select the role that best describes your contribution to this project.
      </p>
      <select
        value={selectedRole}
        onChange={(e) => setSelectedRole(e.target.value)}
        disabled={isMutating}
        className="h-12 w-full rounded border border-zinc-300 bg-zinc-50 px-4 py-3 text-sm text-zinc-700 disabled:border-zinc-300 disabled:bg-zinc-50 disabled:opacity-60"
      >
        <option value="">Select a role...</option>
        {roles.map((role) => (
          <option key={role} value={role}>{role}</option>
        ))}
      </select>
      <div className="mt-2 flex items-center gap-2">
        <button
          type="button"
          onClick={onSave}
          disabled={isMutating || project.projectKey === null || !selectedRole}
          className={setupPrimaryActionButtonClass}
        >
          Save key role
        </button>
      </div>
      {saveMessage && <p className="mt-1 text-sm text-zinc-700">{saveMessage}</p>}
    </div>
  );
}