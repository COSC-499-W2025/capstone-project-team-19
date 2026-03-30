import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import App from "../../App";
import * as uploadsApi from "../../api/uploads";
import { setAuthenticatedTestUser, setRoute } from "./uploadTestUtils";

vi.mock("../../api/uploads", async () => {
  const actual = await vi.importActual<typeof import("../../api/uploads")>("../../api/uploads");
  return {
    ...actual,
    postUploadRun: vi.fn(),
  };
});

const mockedPostUploadRun = vi.mocked(uploadsApi.postUploadRun);

function runResponse(scope: uploadsApi.RunScope, options?: { ready?: boolean; warnings?: uploadsApi.RunWarning[]; errors?: uploadsApi.RunErrorDetail[] }) {
  return {
    success: true as const,
    data: {
      upload_id: 123,
      scope,
      ready: options?.ready ?? true,
      warnings: options?.warnings ?? [],
      errors: options?.errors ?? [],
    },
    error: null,
  };
}

describe("AnalyzePage run sequence", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    setAuthenticatedTestUser();
  });

  // Scenario: prevent accidental run attempts when URL is missing uploadId.
  it("shows missing uploadId guard and does not call run API", async () => {
    setRoute("/upload/analyze");
    render(<App />);

    expect(await screen.findByText("Missing uploadId. Return to Setup and start analysis again.")).toBeInTheDocument();
    await waitFor(() => {
      expect(mockedPostUploadRun).not.toHaveBeenCalled();
    });
  });

  // Scenario: happy-path sequence should execute both scopes and finish cleanly.
  it("runs individual then collaborative scopes and finishes sequence", async () => {
    mockedPostUploadRun
      .mockResolvedValueOnce(runResponse("individual", { ready: true }))
      .mockResolvedValueOnce(runResponse("individual", { ready: true, warnings: [] }))
      .mockResolvedValueOnce(runResponse("collaborative", { ready: true }))
      .mockResolvedValueOnce(runResponse("collaborative", { ready: true, warnings: [] }));

    setRoute("/upload/analyze?uploadId=123");
    render(<App />);

    expect(await screen.findByText("Analysis sequence finished.")).toBeInTheDocument();
    expect(await screen.findByText("Run status: done")).toBeInTheDocument();

    expect(mockedPostUploadRun).toHaveBeenCalledTimes(4);
    expect(mockedPostUploadRun).toHaveBeenNthCalledWith(1, 123, {
      scope: "individual",
      mode: "check",
      force_rerun: false,
    });
    expect(mockedPostUploadRun).toHaveBeenNthCalledWith(2, 123, {
      scope: "individual",
      mode: "run",
      force_rerun: false,
    });
    expect(mockedPostUploadRun).toHaveBeenNthCalledWith(3, 123, {
      scope: "collaborative",
      mode: "check",
      force_rerun: false,
    });
    expect(mockedPostUploadRun).toHaveBeenNthCalledWith(4, 123, {
      scope: "collaborative",
      mode: "run",
      force_rerun: false,
    });
  });

  // Scenario: failure in first scope should short-circuit the remaining sequence.
  it("stops sequence when individual scope fails and does not run collaborative scope", async () => {
    mockedPostUploadRun
      .mockResolvedValueOnce(runResponse("individual", { ready: true }))
      .mockRejectedValueOnce(new Error("Run failed"));

    setRoute("/upload/analyze?uploadId=123");
    render(<App />);

    expect(await screen.findByText("Analysis stopped: individual scope failed.")).toBeInTheDocument();
    expect(await screen.findByText("Run status: failed")).toBeInTheDocument();

    await waitFor(() => {
      expect(mockedPostUploadRun).toHaveBeenCalledTimes(2);
    });
    expect(mockedPostUploadRun).toHaveBeenNthCalledWith(1, 123, {
      scope: "individual",
      mode: "check",
      force_rerun: false,
    });
    expect(mockedPostUploadRun).toHaveBeenNthCalledWith(2, 123, {
      scope: "individual",
      mode: "run",
      force_rerun: false,
    });
  });
});
