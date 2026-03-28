import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import GitHubIntegrationSection from "../GitHubIntegrationSection";
import type { SetupProjectCard } from "../../../types";

const baseProject: SetupProjectCard = {
  projectName: "TestProject",
  projectKey: 1,
  classification: "collaborative",
  projectType: "code",
  gitRepoDetected: true,
  gitCommitCountHint: 10,
  gitAuthorCountHint: 2,
  gitMultiAuthorHint: false,
  gitSelectedIdentityIndices: [],
  githubState: "unset",
  githubRepoLinked: false,
  githubRepoFullName: null,
  mainFileRelpath: null,
  mainSectionIds: [],
  supportingTextRelpaths: [],
  supportingCsvRelpaths: [],
  driveState: "unset",
  driveLinkedFilesCount: 0,
  manualProjectSummary: "",
  manualContributionSummary: "",
  keyRole: "",
  statusLabel: "",
  statusTone: "neutral",
};

function makeActions() {
  return {
    githubStart: vi.fn(),
    githubRepos: vi.fn(),
    githubLink: vi.fn(),
  } as unknown as ReturnType<typeof import("../../../hooks/useSetupFlow")>["actions"];
}

describe("GitHubIntegrationSection", () => {
  beforeEach(() => {
    vi.stubGlobal("window.open", vi.fn(() => ({})));
  });

  it("shows Step 1 when not connected", () => {
    const actions = makeActions();
    render(
      <GitHubIntegrationSection
        project={{ ...baseProject, githubState: "unset" }}
        actions={actions}
        isMutating={false}
        localGitDetected={true}
      />,
    );
    expect(screen.getByText(/Step 1:/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Connect GitHub/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Skip GitHub/i })).toBeInTheDocument();
  });

  it("shows linked repo when already linked", () => {
    render(
      <GitHubIntegrationSection
        project={{
          ...baseProject,
          githubState: "connected",
          githubRepoLinked: true,
          githubRepoFullName: "owner/myrepo",
        }}
        actions={makeActions()}
        isMutating={false}
        localGitDetected={true}
      />,
    );
    expect(screen.getByText(/Linked repo:/)).toBeInTheDocument();
    expect(screen.getByText("owner/myrepo")).toBeInTheDocument();
  });

  it("shows loading spinner when repos are loading", async () => {
    const actions = makeActions();
    actions.githubRepos.mockImplementation(
      () => new Promise(() => {}),
    );
    render(
      <GitHubIntegrationSection
        project={{ ...baseProject, githubState: "connected" }}
        actions={actions}
        isMutating={false}
        localGitDetected={true}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText(/Loading your repositories/i)).toBeInTheDocument();
    });
    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("shows Step 2 with Load repositories when connected and no repos", async () => {
    const actions = makeActions();
    actions.githubRepos.mockResolvedValue({ repos: [] });
    render(
      <GitHubIntegrationSection
        project={{ ...baseProject, githubState: "connected" }}
        actions={actions}
        isMutating={false}
        localGitDetected={true}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText(/Step 2:/)).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /Load repositories/i })).toBeInTheDocument();
  });

  it("shows Step 3, dropdown and Link button when repos are loaded", async () => {
    const actions = makeActions();
    actions.githubRepos.mockResolvedValue({
      repos: [{ full_name: "owner/repo-a" }, { full_name: "owner/repo-b" }],
    });
    render(
      <GitHubIntegrationSection
        project={{ ...baseProject, githubState: "connected" }}
        actions={actions}
        isMutating={false}
        localGitDetected={true}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText(/Step 3:/)).toBeInTheDocument();
    });
    expect(screen.getByPlaceholderText("Select a repository...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Link repository/i })).toBeInTheDocument();
  });

  it("calls githubStart with connectNow true when Connect GitHub is clicked", async () => {
    const user = userEvent.setup();
    const actions = makeActions();
    actions.githubStart.mockResolvedValue({ auth_url: "https://github.com/auth" });
    render(
      <GitHubIntegrationSection
        project={{ ...baseProject, githubState: "unset" }}
        actions={actions}
        isMutating={false}
        localGitDetected={true}
      />,
    );
    await user.click(screen.getByRole("button", { name: /Connect GitHub/i }));
    expect(actions.githubStart).toHaveBeenCalledWith("TestProject", true);
  });

  it("calls githubStart with connectNow false when Skip GitHub is clicked", async () => {
    const user = userEvent.setup();
    const actions = makeActions();
    actions.githubStart.mockResolvedValue({ auth_url: null });
    render(
      <GitHubIntegrationSection
        project={{ ...baseProject, githubState: "unset" }}
        actions={actions}
        isMutating={false}
        localGitDetected={true}
      />,
    );
    await user.click(screen.getByRole("button", { name: /Skip GitHub/i }));
    expect(actions.githubStart).toHaveBeenCalledWith("TestProject", false);
  });

  it("calls onLoadRepos when Load repositories is clicked", async () => {
    const user = userEvent.setup();
    const actions = makeActions();
    actions.githubRepos.mockResolvedValue({ repos: [] });
    render(
      <GitHubIntegrationSection
        project={{ ...baseProject, githubState: "connected" }}
        actions={actions}
        isMutating={false}
        localGitDetected={true}
      />,
    );
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Load repositories/i })).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /Load repositories/i }));
    expect(actions.githubRepos).toHaveBeenCalledWith("TestProject");
  });

  it("shows message when no repositories found", async () => {
    const actions = makeActions();
    actions.githubRepos.mockResolvedValue({ repos: [] });
    render(
      <GitHubIntegrationSection
        project={{ ...baseProject, githubState: "connected" }}
        actions={actions}
        isMutating={false}
        localGitDetected={true}
      />,
    );
    await waitFor(() => {
      expect(screen.getByText(/No repositories found/i)).toBeInTheDocument();
    });
  });
});
