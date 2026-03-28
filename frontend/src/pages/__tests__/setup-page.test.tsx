import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "../../App";
import type { SetupFlowResult, SetupProjectCard } from "../upload/setup/types";
import { useSetupFlow } from "../upload/setup/hooks/useSetupFlow";
import { setAuthenticatedTestUser, setRoute } from "./uploadTestUtils";

vi.mock("../upload/setup/hooks/useSetupFlow", () => ({
  useSetupFlow: vi.fn(),
}));

vi.mock("../upload/setup/components/SetupProjectGroup", () => ({
  default: ({ title }: { title: string }) => <div data-testid={`setup-group-${title.toLowerCase()}`} />,
}));

vi.mock("../upload/hooks/useUnfinishedUploadExitGuard", () => ({
  useUnfinishedUploadExitGuard: vi.fn(),
}));

vi.mock("../upload/upload/recoveryStage", async () => {
  const actual = await vi.importActual<typeof import("../upload/upload/recoveryStage")>(
    "../upload/upload/recoveryStage"
  );
  return {
    ...actual,
    saveUploadRecoveryStage: vi.fn(),
  };
});

const mockedUseSetupFlow = vi.mocked(useSetupFlow);

function makeProjectCard(overrides: Partial<SetupProjectCard> = {}): SetupProjectCard {
  return {
    projectName: "Project Alpha",
    projectKey: 101,
    classification: "individual",
    projectType: "code",
    gitRepoDetected: true,
    gitCommitCountHint: 5,
    gitAuthorCountHint: 1,
    gitMultiAuthorHint: false,
    gitSelectedIdentityIndices: [0],
    githubState: "linked",
    githubRepoLinked: true,
    githubRepoFullName: "example/repo",
    mainFileRelpath: "README.md",
    mainSectionIds: [1],
    supportingTextRelpaths: [],
    supportingCsvRelpaths: [],
    driveState: "skipped",
    driveLinkedFilesCount: 0,
    manualProjectSummary: "summary",
    manualContributionSummary: "contrib",
    keyRole: "Developer",
    statusLabel: "Ready",
    statusTone: "ready",
    ...overrides,
  };
}

function makeFlow(overrides: Partial<SetupFlowResult> = {}): SetupFlowResult {
  const card = makeProjectCard();
  const checkRunReadiness = vi.fn(async () => ({
    upload_id: 123,
    scope: "all" as const,
    ready: true,
    warnings: [],
    errors: [],
  }));

  return {
    upload: {
      upload_id: 123,
      status: "needs_file_roles",
      zip_name: "projects.zip",
      state: {},
    },
    hasValidUploadId: true,
    uploadId: 123,
    uploadStatus: "needs_file_roles",
    externalConsentStatus: "accepted",
    manualOnlySummaries: false,
    loading: false,
    isRefreshing: false,
    isMutating: false,
    loadError: null,
    actionError: null,
    uploadNotFound: false,
    projectCards: [card],
    individualProjects: [card],
    collaborativeProjects: [],
    expandedProjectNames: [],
    onToggleProject: vi.fn(),
    clearActionError: vi.fn(),
    refreshUpload: vi.fn(async () => true),
    actions: {
      getProjectFiles: vi.fn(async () => null),
      setMainFile: vi.fn(async () => null),
      getMainFileSections: vi.fn(async () => null),
      setContributedSections: vi.fn(async () => null),
      setSupportingTextFiles: vi.fn(async () => null),
      setSupportingCsvFiles: vi.fn(async () => null),
      setKeyRole: vi.fn(async () => null),
      getGitIdentities: vi.fn(async () => null),
      saveGitIdentities: vi.fn(async () => null),
      saveManualProjectSummary: vi.fn(async () => null),
      saveManualContributionSummary: vi.fn(async () => null),
      checkRunReadiness,
      githubStart: vi.fn(async () => null),
      githubRepos: vi.fn(async () => null),
      githubLink: vi.fn(async () => null),
      driveStart: vi.fn(async () => null),
      driveFiles: vi.fn(async () => null),
      driveLink: vi.fn(async () => null),
    },
    ...overrides,
  };
}

describe("SetupPage routing and analyze entry", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    setAuthenticatedTestUser();
  });

  it("redirects to /upload/upload when uploadId is missing or invalid", async () => {
    mockedUseSetupFlow.mockReturnValue(
      makeFlow({
        hasValidUploadId: false,
        uploadId: null,
        upload: null,
        uploadStatus: null,
        projectCards: [],
        individualProjects: [],
      })
    );

    setRoute("/upload/setup");
    render(<App />);

    await waitFor(() => {
      expect(window.location.pathname).toBe("/upload/upload");
    });
  });

  it("redirects to /upload/upload when upload context is not found", async () => {
    mockedUseSetupFlow.mockReturnValue(
      makeFlow({
        uploadNotFound: true,
      })
    );

    setRoute("/upload/setup?uploadId=123");
    render(<App />);

    await waitFor(() => {
      expect(window.location.pathname).toBe("/upload/upload");
    });
  });

  it("opens confirm dialog on Analyze when readiness is ready, then navigates on continue", async () => {
    const user = userEvent.setup();
    const flow = makeFlow();
    mockedUseSetupFlow.mockReturnValue(flow);

    setRoute("/upload/setup?uploadId=123");
    render(<App />);

    const analyzeButton = await screen.findByRole("button", { name: "Analyze" });
    await waitFor(() => expect(analyzeButton).toBeEnabled());
    await user.click(analyzeButton);

    expect(await screen.findByText("Confirm Before Continue")).toBeInTheDocument();
    expect(flow.actions.checkRunReadiness).toHaveBeenCalledWith("all");

    await user.click(screen.getByRole("button", { name: "Continue" }));

    await waitFor(() => {
      expect(window.location.pathname).toBe("/upload/analyze");
      expect(window.location.search).toContain("uploadId=123");
    });
  });

  it("uses Open Analyze fast-path when analysis has already started", async () => {
    const user = userEvent.setup();
    mockedUseSetupFlow.mockReturnValue(
      makeFlow({
        upload: {
          upload_id: 123,
          status: "analyzing",
          zip_name: "projects.zip",
          state: {},
        },
        uploadStatus: "analyzing",
      })
    );

    setRoute("/upload/setup?uploadId=123");
    render(<App />);

    const openAnalyzeButton = await screen.findByRole("button", { name: "Open Analyze" });
    await waitFor(() => expect(openAnalyzeButton).toBeEnabled());
    await user.click(openAnalyzeButton);

    await waitFor(() => {
      expect(window.location.pathname).toBe("/upload/analyze");
      expect(window.location.search).toContain("uploadId=123");
    });
    expect(screen.queryByText("Confirm Before Continue")).not.toBeInTheDocument();
  });
});
