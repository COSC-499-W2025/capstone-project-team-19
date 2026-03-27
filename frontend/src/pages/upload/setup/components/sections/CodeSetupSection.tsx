import { useEffect, useMemo, useState } from "react";
import type { GitIdentityOption } from "../../../../../api/uploads";
import type { SetupFlowResult, SetupProjectCard } from "../../types";
import GitHubIntegrationSection from "./GitHubIntegrationSection";

type Props = {
  project: SetupProjectCard;
  actions: SetupFlowResult["actions"];
  isMutating: boolean;
};

function formatIdentityLabel(option: GitIdentityOption): string {
  const name = option.name?.trim() || "Unknown Author";
  const email = option.email?.trim() || "no-email";
  return `${name} (${email})`;
}

function parseExtraEmails(raw: string): string[] {
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export default function CodeSetupSection({ project, actions, isMutating }: Props) {
  const [identities, setIdentities] = useState<GitIdentityOption[]>([]);
  const [selectedIndices, setSelectedIndices] = useState<number[]>(project.gitSelectedIdentityIndices);
  const [extraEmails, setExtraEmails] = useState("");
  const [identitiesLoading, setIdentitiesLoading] = useState(false);
  const [identityMessage, setIdentityMessage] = useState<string | null>(null);
  const [localGitDetected, setLocalGitDetected] = useState<boolean | null>(null);

  const canPickIdentities =
    project.classification === "collaborative" &&
    localGitDetected === true &&
    identities.length > 0;

  const gitCommitCount = useMemo(
    () => identities.reduce((sum, option) => sum + (option.commit_count || 0), 0),
    [identities],
  );

  useEffect(() => {
    setSelectedIndices(project.gitSelectedIdentityIndices);
  }, [project.gitSelectedIdentityIndices]);

  // Detect local .git and load contributor identities
  useEffect(() => {
    if (project.projectKey === null) {
      setLocalGitDetected(null);
      setIdentities([]);
      return;
    }

    let active = true;

    async function detectContributors() {
      setIdentitiesLoading(true);
      setIdentityMessage(null);

      const gitData = await actions.getGitIdentities(project.projectKey as number);
      if (!active) return;

      if (gitData) {
        setLocalGitDetected(true);
        setIdentities(gitData.options);
        setSelectedIndices(gitData.selected_indices);
      } else {
        setLocalGitDetected(false);
        setIdentities([]);
        setSelectedIndices([]);
      }
      setIdentitiesLoading(false);
    }

    detectContributors();
    return () => {
      active = false;
    };
  }, [actions, project.projectKey]);

  const identitySummary = useMemo(() => {
    if (identitiesLoading) return "Detecting local .git repository...";
    if (localGitDetected === true) return ".git file is detected in this project.";
    return "No local .git repository detected for this project.";
  }, [identitiesLoading, localGitDetected]);

  function onToggleIdentity(index: number) {
    setSelectedIndices((prev) =>
      prev.includes(index) ? prev.filter((item) => item !== index) : [...prev, index].sort((a, b) => a - b),
    );
  }

  async function onSaveIdentities() {
    if (!canPickIdentities || project.projectKey === null) return;
    const data = await actions.saveGitIdentities(
      project.projectKey,
      selectedIndices,
      parseExtraEmails(extraEmails),
    );
    if (!data) return;
    setSelectedIndices(data.selected_indices);
    setIdentities(data.options);
    setIdentityMessage("Identity selection saved.");
  }

  return (
    <div className="space-y-4">
      {/* --- Git Detection --- */}
      <div className="space-y-2">
        <h4 className="text-lg leading-tight font-semibold text-zinc-900">Git Detection</h4>
        <p className="text-sm leading-relaxed text-zinc-700">{identitySummary}</p>
      </div>

      {project.classification === "collaborative" && localGitDetected && (
        <p className="text-sm leading-relaxed text-zinc-600">
          Commits: {gitCommitCount} | Authors: {identities.length}
        </p>
      )}

      {/* --- Identity picker (collaborative projects with a .git repo) --- */}
      {canPickIdentities && (
        <div className="space-y-3">
          <div className="text-sm font-semibold text-zinc-900">Select your identity (collaborative code)</div>
          {identities.map((option) => (
            <label key={option.index} className="flex items-center gap-2 text-sm text-zinc-800">
              <input
                type="checkbox"
                checked={selectedIndices.includes(option.index)}
                onChange={() => onToggleIdentity(option.index)}
                disabled={isMutating}
              />
              <span>
                {formatIdentityLabel(option)} - {option.commit_count} commits
              </span>
            </label>
          ))}

          <div className="space-y-1">
            <label className="text-sm font-medium text-zinc-700" htmlFor={`extra-emails-${project.projectName}`}>
              Extra commit emails (comma-separated)
            </label>
            <input
              id={`extra-emails-${project.projectName}`}
              type="text"
              value={extraEmails}
              onChange={(event) => setExtraEmails(event.target.value)}
              placeholder="you@school.ca, work@company.com"
              className="h-12 w-full rounded border border-zinc-300 !bg-zinc-50 !px-4 !py-3 text-sm text-zinc-700 placeholder:text-zinc-400 disabled:!bg-zinc-50"
              disabled={isMutating}
            />
          </div>

          <button
            type="button"
            onClick={onSaveIdentities}
            disabled={isMutating || project.projectKey === null}
            className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
          >
            Save identity selection
          </button>
          {identityMessage && <p className="text-sm text-zinc-700">{identityMessage}</p>}
        </div>
      )}

      {/* --- GitHub Integration (connect, load repos, link) --- */}
      <GitHubIntegrationSection
        project={project}
        actions={actions}
        isMutating={isMutating}
        localGitDetected={localGitDetected}
      />
    </div>
  );
}
