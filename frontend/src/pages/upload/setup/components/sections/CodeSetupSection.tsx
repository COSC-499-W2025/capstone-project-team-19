import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
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
  const [repoSearchQuery, setRepoSearchQuery] = useState("");
  const [repoListOpen, setRepoListOpen] = useState(false);
  const repoListRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [dropdownStyle, setDropdownStyle] = useState<{ bottom: number; left: number; width: number } | null>(null);

  const filteredRepos = useMemo(() => {
    const q = repoSearchQuery.trim().toLowerCase();
    if (!q) return repos;
    return repos.filter((r) => r.full_name.toLowerCase().includes(q));
  }, [repos, repoSearchQuery]);

  const hideRepoList = useCallback(() => {
    setRepoListOpen(false);
  }, []);

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
    const fullName = project.githubRepoFullName ?? "";
    setSelectedRepo(fullName);
    if (fullName) setRepoSearchQuery(fullName);
  }, [project.githubRepoFullName]);

  useLayoutEffect(() => {
    if (repoListOpen && inputRef.current) {
      const rect = inputRef.current.getBoundingClientRect();
      setDropdownStyle({
        bottom: window.innerHeight - rect.top + 4,
        left: rect.left,
        width: rect.width,
      });
    } else {
      setDropdownStyle(null);
    }
  }, [repoListOpen]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      const target = e.target as Node;
      const inInput = inputRef.current?.contains(target);
      const inDropdown = dropdownRef.current?.contains(target);
      if (!inInput && !inDropdown) {
        hideRepoList();
      }
    }
    function handleScroll(e: Event) {
      const target = e.target as Node;
      if (dropdownRef.current?.contains(target)) return;
      hideRepoList();
    }
    if (repoListOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      window.addEventListener("scroll", handleScroll, true);
      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
        window.removeEventListener("scroll", handleScroll, true);
      };
    }
  }, [repoListOpen, hideRepoList]);

  useEffect(() => {
    if (
      project.githubState !== "connected" ||
      repos.length > 0 ||
      reposLoading ||
      project.githubRepoLinked
    ) {
      return;
    }
    let active = true;
    setReposLoading(true);
    setGithubMessage(null);
    actions
      .githubRepos(project.projectName)
      .then((data) => {
        if (!active || !data) return;
        setRepos(data.repos);
        setGithubMessage(data.repos.length > 0 ? "Repositories loaded. Search and select one, then click Link." : "No repositories found.");
      })
      .finally(() => {
        if (active) setReposLoading(false);
      });
    return () => {
      active = false;
    };
  }, [project.githubState, project.githubRepoLinked, project.projectName, actions]);

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
      const opened = window.open(data.auth_url, "_blank");
      if (opened) {
        setGithubMessage("Authorize in the new tab. It will close automatically when done.");
      } else {
        setGithubMessage("Popup was blocked. Click the link below to authorize.");
      }
      setGithubMessage("Click “Open GitHub Authorization” to authorize in your browser.");
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
    setGithubMessage(data.repos.length > 0 ? "Repositories loaded. Search and select one, then click Link." : "No repositories found.");
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
        {project.githubRepoLinked && project.githubRepoFullName ? (
          <p className="text-sm text-zinc-700">
            Linked repo: <span className="font-medium">{project.githubRepoFullName}</span>
          </p>
        ) : (
          <>
            {project.githubState !== "connected" ? (
              <div className="space-y-2">
                <p className="text-sm text-zinc-700">
                  <strong>Step 1:</strong> Connect your GitHub account to fetch your repositories.
                </p>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => onGithubStart(true)}
                    disabled={isMutating}
                    className="rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
                  >
                    Connect GitHub
                  </button>
                  <button
                    type="button"
                    onClick={() => onGithubStart(false)}
                    disabled={isMutating}
                    className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-50 disabled:opacity-50"
                  >
                    Skip GitHub
                  </button>
                </div>
              </div>
            ) : reposLoading ? (
              <p className="text-sm text-zinc-700">Loading your repositories...</p>
            ) : repos.length === 0 ? (
              <div className="space-y-2">
                <p className="text-sm text-zinc-700">
                  <strong>Step 2:</strong> Load your repositories from GitHub.
                </p>
                <button
                  type="button"
                  onClick={onLoadRepos}
                  disabled={isMutating || reposLoading}
                  className="rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
                >
                  Load repositories
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-zinc-700">
                  <strong>Step 3:</strong> Select the repo that matches this project and link it.
                </p>
              </div>
            )}
            {authUrl && (
              <a
                href={authUrl}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-[#0969da] hover:underline"
              >
                Open GitHub Authorization (if the tab didn&apos;t open)
              </a>
            )}
          </>
        )}
        {!localGitDetected && project.classification === "collaborative" && (
          <p className="text-sm text-zinc-600">
            With no local .git history, collaborative identity is inferred from the connected GitHub account during analysis.
          </p>
        )}

        {repos.length > 0 && (
          <div className="space-y-2" ref={repoListRef}>
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                value={repoListOpen ? repoSearchQuery : selectedRepo || ""}
                onChange={(e) => {
                  setRepoSearchQuery(e.target.value);
                  setRepoListOpen(true);
                }}
                onFocus={() => setRepoListOpen(true)}
                placeholder="Select a repository..."
                className="h-12 w-full rounded border border-zinc-300 bg-zinc-50 px-4 py-3 pr-10 text-sm text-zinc-700 placeholder:text-zinc-400"
                disabled={isMutating}
                aria-expanded={repoListOpen}
                aria-haspopup="listbox"
                aria-label="Search repositories"
              />
              <span
                className="absolute right-3 top-1/2 -translate-y-1/2 cursor-pointer text-zinc-500"
                onClick={() => inputRef.current?.focus()}
                role="button"
                aria-label={repoListOpen ? "Close repository list" : "Open repository list"}
              >
                {repoListOpen ? (
                  <svg className="h-4 w-4" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M3 6 L8 11 L13 6 Z" />
                  </svg>
                ) : (
                  <svg className="h-4 w-4" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M3 10 L8 5 L13 10 Z" />
                  </svg>
                )}
              </span>
              {repoListOpen &&
                dropdownStyle &&
                createPortal(
                  <div
                    ref={dropdownRef}
                    className="fixed z-[9999] max-h-48 overflow-y-auto rounded border border-zinc-300 bg-white shadow-lg"
                    role="listbox"
                    style={{
                      bottom: dropdownStyle.bottom,
                      left: dropdownStyle.left,
                      width: dropdownStyle.width,
                    }}
                  >
                    {filteredRepos.length === 0 ? (
                      <div className="px-4 py-3 text-sm text-zinc-500">No matching repositories</div>
                    ) : (
                      filteredRepos.map((repo) => (
                        <button
                          key={repo.full_name}
                          type="button"
                          role="option"
                          aria-selected={selectedRepo === repo.full_name}
                          className={`block w-full px-4 py-2.5 text-left text-sm hover:bg-zinc-100 ${
                            selectedRepo === repo.full_name ? "bg-zinc-100 font-medium" : "text-zinc-700"
                          }`}
                          onClick={() => {
                            setSelectedRepo(repo.full_name);
                            setRepoSearchQuery(repo.full_name);
                            setRepoListOpen(false);
                          }}
                        >
                          {repo.full_name}
                        </button>
                      ))
                    )}
                  </div>,
                  document.body,
                )}
            </div>
            <button
              type="button"
              onClick={onLinkRepo}
              disabled={isMutating || !selectedRepo}
              className="rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
            >
              Link repository
            </button>
          </div>
        )}

        {githubMessage && <p className="text-sm text-zinc-700">{githubMessage}</p>}
      </div>
    </div>
  );
}
