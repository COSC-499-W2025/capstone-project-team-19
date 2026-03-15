import { useEffect, useMemo, useState } from "react";
import type { GitHubRepo, GitIdentityOption } from "../../../../../api/uploads";
import type { SetupFlowResult, SetupProjectCard } from "../../types";

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

  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState(project.githubRepoFullName ?? "");
  const [reposLoading, setReposLoading] = useState(false);
  const [authUrl, setAuthUrl] = useState<string | null>(null);
  const [githubMessage, setGithubMessage] = useState<string | null>(null);

  const canPickIdentities = project.classification === "collaborative";
  const shouldSuggestIdentitySelection = canPickIdentities && project.gitRepoDetected === true && project.gitMultiAuthorHint;

  useEffect(() => {
    setSelectedIndices(project.gitSelectedIdentityIndices);
  }, [project.gitSelectedIdentityIndices]);

  useEffect(() => {
    setSelectedRepo(project.githubRepoFullName ?? "");
  }, [project.githubRepoFullName]);

  useEffect(() => {
    if (!shouldSuggestIdentitySelection || project.projectKey === null) {
      setIdentities([]);
      return;
    }

    let active = true;

    async function loadIdentities() {
      setIdentitiesLoading(true);
      setIdentityMessage(null);
      const data = await actions.getGitIdentities(project.projectKey as number);
      if (!active) return;

      if (!data) {
        setIdentities([]);
        setIdentitiesLoading(false);
        return;
      }

      setIdentities(data.options);
      setSelectedIndices(data.selected_indices);
      setIdentitiesLoading(false);
    }

    loadIdentities();
    return () => {
      active = false;
    };
  }, [actions, project.projectKey, shouldSuggestIdentitySelection]);

  const identitySummary = useMemo(() => {
    if (project.gitRepoDetected === false) return "No local .git repository detected for this project.";
    if (project.gitRepoDetected === true) return ".git file is detected in this project.";
    return "Git detection data not available yet.";
  }, [project.gitRepoDetected]);

  function onToggleIdentity(index: number) {
    setSelectedIndices((prev) =>
      prev.includes(index) ? prev.filter((item) => item !== index) : [...prev, index].sort((a, b) => a - b),
    );
  }

  async function onSaveIdentities() {
    if (project.projectKey === null) return;
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

  async function onGithubStart(connectNow: boolean) {
    setGithubMessage(null);
    const data = await actions.githubStart(project.projectName, connectNow);
    if (!data) return;

    setAuthUrl(data.auth_url ?? null);
    if (!connectNow) {
      setGithubMessage("GitHub integration skipped for now.");
      return;
    }

    if (data.auth_url) {
      setGithubMessage("Continue with GitHub OAuth using the link below.");
      return;
    }

    setGithubMessage("GitHub is connected.");
  }

  async function onLoadRepos() {
    setReposLoading(true);
    setGithubMessage(null);
    const data = await actions.githubRepos(project.projectName);
    setReposLoading(false);
    if (!data) return;

    setRepos(data.repos);
    if (!selectedRepo && data.repos.length > 0) {
      setSelectedRepo(data.repos[0].full_name);
    }
    setGithubMessage(data.repos.length > 0 ? "Repositories loaded." : "No repositories found.");
  }

  async function onLinkRepo() {
    if (!selectedRepo) return;
    const data = await actions.githubLink(project.projectName, selectedRepo);
    if (!data) return;
    setGithubMessage("Repository linked.");
  }

  return (
    <div className="space-y-3 rounded-lg border border-zinc-200 bg-white px-3 py-2">
      <h4 className="text-sm leading-tight font-semibold text-zinc-900">Code Setup</h4>

      <p className="text-xs leading-relaxed text-zinc-700">{identitySummary}</p>

      {project.gitRepoDetected === true && (
        <p className="text-xs leading-relaxed text-zinc-600">
          Commits: {project.gitCommitCountHint} | Authors: {project.gitAuthorCountHint}
        </p>
      )}

      {project.classification === "individual" && (
        <p className="rounded border border-zinc-200 bg-zinc-50 px-2 py-1 text-xs text-zinc-700">
          Identity selection is not shown for individual code projects (CLI-aligned behavior).
        </p>
      )}

      {project.classification === "collaborative" && !shouldSuggestIdentitySelection && (
        <p className="rounded border border-zinc-200 bg-zinc-50 px-2 py-1 text-xs text-zinc-700">
          Identity selection is only needed when a local multi-author git history is detected.
        </p>
      )}

      {shouldSuggestIdentitySelection && (
        <div className="space-y-2 rounded border border-zinc-200 bg-zinc-50 px-2 py-2">
          <div className="text-xs font-semibold text-zinc-900">Select your git identity (collaborative only)</div>
          {identitiesLoading && <p className="text-xs text-zinc-600">Loading identities...</p>}
          {!identitiesLoading && identities.length === 0 && (
            <p className="text-xs text-zinc-600">No identities detected yet.</p>
          )}
          {!identitiesLoading &&
            identities.map((option) => (
              <label key={option.index} className="flex items-center gap-2 text-xs text-zinc-800">
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
            <label className="text-xs font-medium text-zinc-700" htmlFor={`extra-emails-${project.projectName}`}>
              Extra commit emails (comma-separated)
            </label>
            <input
              id={`extra-emails-${project.projectName}`}
              type="text"
              value={extraEmails}
              onChange={(event) => setExtraEmails(event.target.value)}
              placeholder="you@school.ca, work@company.com"
              className="h-8 w-full rounded border border-zinc-300 bg-white px-2 text-xs"
              disabled={isMutating}
            />
          </div>

          <button
            type="button"
            onClick={onSaveIdentities}
            disabled={isMutating || project.projectKey === null}
            className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
          >
            Save identity selection
          </button>
          {identityMessage && <p className="text-xs text-zinc-700">{identityMessage}</p>}
        </div>
      )}

      <div className="space-y-2 rounded border border-zinc-200 bg-zinc-50 px-2 py-2">
        <div className="text-xs font-semibold text-zinc-900">GitHub Integration</div>
        <p className="text-xs text-zinc-700">
          State: <span className="font-medium">{project.githubState}</span>
          {project.githubRepoLinked && project.githubRepoFullName ? ` | Linked repo: ${project.githubRepoFullName}` : ""}
        </p>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onGithubStart(true)}
            disabled={isMutating}
            className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
          >
            Connect GitHub
          </button>
          <button
            type="button"
            onClick={() => onGithubStart(false)}
            disabled={isMutating}
            className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
          >
            Skip for now
          </button>
          <button
            type="button"
            onClick={onLoadRepos}
            disabled={isMutating || reposLoading}
            className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
          >
            {reposLoading ? "Loading..." : "Load repositories"}
          </button>
        </div>

        {authUrl && (
          <a href={authUrl} target="_blank" rel="noreferrer" className="text-xs font-medium text-blue-700 underline">
            Open GitHub authorization
          </a>
        )}

        {repos.length > 0 && (
          <div className="space-y-2">
            <select
              value={selectedRepo}
              onChange={(event) => setSelectedRepo(event.target.value)}
              className="h-8 w-full rounded border border-zinc-300 bg-white px-2 text-xs"
              disabled={isMutating}
            >
              {repos.map((repo) => (
                <option key={repo.full_name} value={repo.full_name}>
                  {repo.full_name}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={onLinkRepo}
              disabled={isMutating || !selectedRepo}
              className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs font-medium text-zinc-900 disabled:opacity-50"
            >
              Link selected repository
            </button>
          </div>
        )}

        {githubMessage && <p className="text-xs text-zinc-700">{githubMessage}</p>}
      </div>
    </div>
  );
}
