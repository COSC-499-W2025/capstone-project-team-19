import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "../../App";
import * as uploadsApi from "../../api/uploads";
import * as recoveryStage from "../upload/upload/recoveryStage";
import { setAuthenticatedTestUser, setRoute } from "./uploadTestUtils";

vi.mock("../../api/uploads", async () => {
  const actual = await vi.importActual<typeof import("../../api/uploads")>("../../api/uploads");
  return {
    ...actual,
    getUploads: vi.fn(),
    deleteUpload: vi.fn(),
    getUploadStatus: vi.fn(),
  };
});

vi.mock("../upload/upload/recoveryStage", async () => {
  const actual = await vi.importActual<typeof import("../upload/upload/recoveryStage")>(
    "../upload/upload/recoveryStage"
  );
  return {
    ...actual,
    saveUploadRecoveryStage: vi.fn(),
    readUploadRecoveryStage: vi.fn(() => null),
    clearUploadRecoveryStage: vi.fn(),
    recoveryRouteForUpload: vi.fn(() => "/upload/upload"),
  };
});

vi.mock("../upload/hooks/useUnfinishedUploadExitGuard", () => ({
  useUnfinishedUploadExitGuard: vi.fn(),
}));

const mockedGetUploads = vi.mocked(uploadsApi.getUploads);
const mockedDeleteUpload = vi.mocked(uploadsApi.deleteUpload);
const mockedGetUploadStatus = vi.mocked(uploadsApi.getUploadStatus);
const mockedReadUploadRecoveryStage = vi.mocked(recoveryStage.readUploadRecoveryStage);
const mockedClearUploadRecoveryStage = vi.mocked(recoveryStage.clearUploadRecoveryStage);
const mockedRecoveryRouteForUpload = vi.mocked(recoveryStage.recoveryRouteForUpload);

function makeUploadsResponse(uploads: uploadsApi.UploadListItem[]) {
  return {
    success: true as const,
    data: { uploads },
    error: null,
  };
}

function makeUnfinishedUpload(): uploadsApi.UploadListItem {
  return {
    upload_id: 42,
    status: "parsed",
    zip_name: "my-projects.zip",
    created_at: "2026-03-08T00:00:00",
  };
}

describe("UploadPage recovery and validation flows", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    setAuthenticatedTestUser();

    mockedGetUploads.mockResolvedValue(makeUploadsResponse([]));
    mockedDeleteUpload.mockResolvedValue({
      success: true,
      data: null,
      error: null,
    });
    mockedGetUploadStatus.mockImplementation(async (uploadId: number) => ({
      success: true,
      data: {
        upload_id: uploadId,
        status: "parsed",
        zip_name: "recovered.zip",
        state: {},
      },
      error: null,
    }));
    mockedReadUploadRecoveryStage.mockReturnValue(null);
    mockedRecoveryRouteForUpload.mockReturnValue("/upload/upload?uploadId=42&stage=projects");
  });

  it("shows a validation error when a non-zip file is selected", async () => {
    setRoute("/upload/upload");
    const { container } = render(<App />);

    await screen.findByText("Only ZIP files are accepted.");
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement | null;
    expect(fileInput).not.toBeNull();

    const nonZipFile = new File(["hello"], "notes.txt", { type: "text/plain" });
    fireEvent.change(fileInput as HTMLInputElement, { target: { files: [nonZipFile] } });

    expect(await screen.findByText("Only ZIP files are allowed.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  it("shows unfinished upload recovery dialog when a recoverable upload exists", async () => {
    mockedGetUploads.mockResolvedValueOnce(makeUploadsResponse([makeUnfinishedUpload()]));

    setRoute("/upload/upload");
    render(<App />);

    expect(await screen.findByText("Unfinished Upload Found")).toBeInTheDocument();
    expect(screen.getByText(/Resume where you left off, or start a new upload\./)).toBeInTheDocument();
    expect(mockedGetUploads).toHaveBeenCalledWith(10, 0);
  });

  it("resumes unfinished upload using recovery route", async () => {
    const user = userEvent.setup();
    mockedGetUploads.mockResolvedValueOnce(makeUploadsResponse([makeUnfinishedUpload()]));
    mockedReadUploadRecoveryStage.mockReturnValue("classification");
    mockedRecoveryRouteForUpload.mockReturnValue("/upload/upload?uploadId=42&stage=classification");

    setRoute("/upload/upload");
    render(<App />);

    await screen.findByText("Unfinished Upload Found");
    await user.click(screen.getByRole("button", { name: "Resume" }));

    await waitFor(() => {
      expect(window.location.pathname).toBe("/upload/upload");
      expect(window.location.search).toContain("uploadId=42");
      expect(window.location.search).toContain("stage=classification");
    });
    expect(mockedReadUploadRecoveryStage).toHaveBeenCalledWith(42);
    expect(mockedRecoveryRouteForUpload).toHaveBeenCalled();
  });

  it("deletes unfinished upload when Start New is selected", async () => {
    const user = userEvent.setup();
    mockedGetUploads.mockResolvedValueOnce(makeUploadsResponse([makeUnfinishedUpload()]));

    setRoute("/upload/upload");
    render(<App />);

    await screen.findByText("Unfinished Upload Found");
    await user.click(screen.getByRole("button", { name: "Start New" }));

    await waitFor(() => {
      expect(mockedDeleteUpload).toHaveBeenCalledWith(42);
      expect(mockedClearUploadRecoveryStage).toHaveBeenCalledWith(42);
    });
    await waitFor(() => {
      expect(screen.queryByText("Unfinished Upload Found")).not.toBeInTheDocument();
    });
  });

  it("shows recovery error when deleting unfinished upload fails", async () => {
    const user = userEvent.setup();
    mockedGetUploads.mockResolvedValueOnce(makeUploadsResponse([makeUnfinishedUpload()]));
    mockedDeleteUpload.mockResolvedValueOnce({
      success: false,
      data: null,
      error: { message: "Could not remove upload.", code: 500 },
    });

    setRoute("/upload/upload");
    render(<App />);

    await screen.findByText("Unfinished Upload Found");
    await user.click(screen.getByRole("button", { name: "Start New" }));

    expect(await screen.findByText("Could not remove upload.")).toBeInTheDocument();
    expect(screen.getByText("Unfinished Upload Found")).toBeInTheDocument();
  });
});
