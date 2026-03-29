import { useEffect, useState } from "react";
import type { GitHubRepo } from "../../../../../api/uploads";
import type { SetupFlowResult, SetupProjectCard } from "../../types";
import RepoSearchDropdown from "../RepoSearchDropdown";

type Props = {
  project: SetupProjectCard;
  actions: SetupFlowResult["actions"];
  isMutating: boolean;
  localGitDetected: boolean | null;
};

const BTN_PRIMARY = "rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50";
const BTN_SECONDARY = "rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-50 disabled:opacity-50";

export default function GitHubIntegrationSection({ project, actions, isMutating, localGitDetected }: Props) {
  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState(project.githubRepoFullName ?? "");
  const [reposLoading, setReposLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // Sync external repo name into local state (e.g. after a refresh)
  useEffect(() => {
    const fullName = project.githubRepoFullName ?? "";
    setSelectedRepo(fullName);
  }, [project.githubRepoFullName]);

  // Auto-load repos after returning from OAuth (githubState flips to "connected")
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
    setMessage(null);
    actions
      .githubRepos(project.projectName)
      .then((data) => {
        if (!active || !data) return;
        setRepos(data.repos);
        setMessage(
          data.repos.length > 0
            ? "Repositories loaded. Search and select one, then click Link."
            : "No repositories found.",
        );
      })
      .finally(() => {
        if (active) setReposLoading(false);
      });
    return () => {
      active = false;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps -- repos.length and reposLoading are guards, not triggers
  }, [project.githubState, project.githubRepoLinked, project.projectName, actions]);

  async function onConnect(connectNow: boolean) {
    setMessage(null);
    const data = await actions.githubStart(project.projectName, connectNow);
    if (!data) return;

    if (!connectNow) {
      setMessage("GitHub integration skipped for now.");
      return;
    }

    if (data.auth_url) {
      const opened = window.open(data.auth_url, "_blank");
      setMessage(
        opened
          ? "Authorize in the new tab. It will close automatically when done."
          : "Popup was blocked. Try Connect GitHub again or allow popups for this site.",
      );
      return;
    }

    setMessage("GitHub is connected.");
  }

  async function onLoadRepos() {
    setReposLoading(true);
    setMessage(null);
    const data = await actions.githubRepos(project.projectName);
    setReposLoading(false);
    if (!data) return;
    setRepos(data.repos);
    setMessage(
      data.repos.length > 0
        ? "Repositories loaded. Search and select one, then click Link."
        : "No repositories found.",
    );
  }

  async function onLinkRepo() {
    if (!selectedRepo) return;
    const data = await actions.githubLink(project.projectName, selectedRepo);
    if (!data) return;
    setMessage("Repository linked.");
  }

  // --- Render helpers ---

  const linked = project.githubRepoLinked && project.githubRepoFullName;

  return (
    <div className="space-y-3">
      <h4 className="text-lg leading-tight font-semibold text-zinc-900">GitHub Integration</h4>

      {linked ? (
        <p className="text-sm text-zinc-700">
          Linked repo: <span className="font-medium">{project.githubRepoFullName}</span>
        </p>
      ) : (
        <StepContent
          githubState={project.githubState}
          reposLoading={reposLoading}
          reposCount={repos.length}
          isMutating={isMutating}
          onConnect={onConnect}
          onLoadRepos={onLoadRepos}
        />
      )}

      {!localGitDetected && project.classification === "collaborative" && (
        <p className="text-sm text-zinc-600">
          With no local .git history, collaborative identity is inferred from the connected GitHub
          account during analysis.
        </p>
      )}

      {repos.length > 0 && (
        <div className="space-y-2">
          <RepoSearchDropdown
            repos={repos}
            selectedRepo={selectedRepo}
            onSelect={setSelectedRepo}
            disabled={isMutating}
          />
          <button
            type="button"
            onClick={onLinkRepo}
            disabled={isMutating || !selectedRepo}
            className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 hover:bg-zinc-50 disabled:opacity-50"
          >
            Link repository
          </button>
        </div>
      )}

      {message && <p className="text-sm text-zinc-700">{message}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: renders only the step-appropriate prompt + buttons
// ---------------------------------------------------------------------------

function StepContent({
  githubState,
  reposLoading,
  reposCount,
  isMutating,
  onConnect,
  onLoadRepos,
}: {
  githubState: string;
  reposLoading: boolean;
  reposCount: number;
  isMutating: boolean;
  onConnect: (connectNow: boolean) => void;
  onLoadRepos: () => void;
}) {
  if (githubState !== "connected") {
    return (
      <div className="space-y-2">
        <p className="text-sm text-zinc-700">
          <strong>Step 1:</strong> Connect your GitHub account to fetch your repositories.
        </p>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => onConnect(true)} disabled={isMutating} className={BTN_PRIMARY}>
            Connect GitHub
          </button>
          <button type="button" onClick={() => onConnect(false)} disabled={isMutating} className={BTN_SECONDARY}>
            Skip GitHub
          </button>
        </div>
      </div>
    );
  }

  if (reposLoading) {
    return (
      <div className="flex items-center gap-2">
        <span
          className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-600"
          aria-hidden
        />
        <p className="text-sm text-zinc-700">Loading your repositories...</p>
      </div>
    );
  }

  if (reposCount === 0) {
    return (
      <div className="space-y-2">
        <p className="text-sm text-zinc-700">
          <strong>Step 2:</strong> Load your repositories from GitHub.
        </p>
        <button type="button" onClick={onLoadRepos} disabled={isMutating} className={BTN_PRIMARY}>
          Load repositories
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-sm text-zinc-700">
        <strong>Step 3:</strong> Select the repo that matches this project and link it.
      </p>
    </div>
  );
}
