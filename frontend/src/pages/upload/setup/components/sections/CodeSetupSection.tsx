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
  const [localGitDetected, setLocalGitDetected] = useState<boolean | null>(null);

  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState(project.githubRepoFullName ?? "");
  const [reposLoading, setReposLoading] = useState(false);
  const [authUrl, setAuthUrl] = useState<string | null>(null);
  const [githubMessage, setGithubMessage] = useState<string | null>(null);

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

  useEffect(() => {
    setSelectedRepo(project.githubRepoFullName ?? "");
  }, [project.githubRepoFullName]);

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
        setIdentitiesLoading(false);
        return;
      }

      setLocalGitDetected(false);
      setIdentities([]);
      setSelectedIndices([]);
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
    <div className="space-y-4">
      <div className="space-y-2">
        <h4 className="text-lg leading-tight font-semibold text-zinc-900">Git Detection</h4>
        <p className="text-sm leading-relaxed text-zinc-700">{identitySummary}</p>
      </div>

      {project.classification === "collaborative" && localGitDetected && (
        <p className="text-sm leading-relaxed text-zinc-600">
          Commits: {gitCommitCount} | Authors: {identities.length}
        </p>
      )}

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

      <div className="space-y-3">
        <h4 className="text-lg leading-tight font-semibold text-zinc-900">GitHub Integration</h4>
        <p className="text-sm text-zinc-700">
          State: <span className="font-medium">{project.githubState}</span>
          {project.githubRepoLinked && project.githubRepoFullName ? ` | Linked repo: ${project.githubRepoFullName}` : ""}
        </p>
        {!localGitDetected && project.classification === "collaborative" && (
          <p className="text-sm text-zinc-700">
            With no local .git history, collaborative identity is inferred from the connected GitHub account during analysis.
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onGithubStart(true)}
            disabled={isMutating}
            className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
          >
            Connect GitHub
          </button>
          <button
            type="button"
            onClick={() => onGithubStart(false)}
            disabled={isMutating}
            className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
          >
            Skip for now
          </button>
          <button
            type="button"
            onClick={onLoadRepos}
            disabled={isMutating || reposLoading}
            className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
          >
            {reposLoading ? "Loading..." : "Load repositories"}
          </button>
        </div>

        {authUrl && (
          <a href={authUrl} target="_blank" rel="noreferrer" className="text-sm font-medium text-blue-700 underline">
            Open GitHub authorization
          </a>
        )}

        {repos.length > 0 && (
          <div className="space-y-2">
            <select
              value={selectedRepo}
              onChange={(event) => setSelectedRepo(event.target.value)}
              className="h-12 w-full rounded border border-zinc-300 bg-zinc-50 px-4 py-3 text-sm text-zinc-700"
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
              className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 disabled:opacity-50"
            >
              Link selected repository
            </button>
          </div>
        )}

        {githubMessage && <p className="text-sm text-zinc-700">{githubMessage}</p>}
      </div>
    </div>
  );
}
