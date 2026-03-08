import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "../../App";
import * as consentApi from "../../api/consent";

vi.mock("../../api/consent", () => ({
  getConsentStatus: vi.fn(),
  postInternalConsent: vi.fn(),
  postExternalConsent: vi.fn(),
}));

const mockedGetConsentStatus = vi.mocked(consentApi.getConsentStatus);
const mockedPostInternalConsent = vi.mocked(consentApi.postInternalConsent);
const mockedPostExternalConsent = vi.mocked(consentApi.postExternalConsent);

function setRoute(path: string) {
  window.history.pushState({}, "", path);
}

describe("upload wizard flow", () => {
  beforeEach(() => {
    localStorage.setItem("resuME_token", "test-token");

    mockedGetConsentStatus.mockResolvedValue({
      success: true,
      data: {
        user_id: 1,
        internal_consent: null,
        external_consent: null,
      },
      error: null,
    });

    mockedPostInternalConsent.mockResolvedValue({
      success: true,
      data: {
        consent_id: 1,
        user_id: 1,
        status: "accepted",
        timestamp: "2026-03-08T00:00:00",
      },
      error: null,
    });

    mockedPostExternalConsent.mockResolvedValue({
      success: true,
      data: {
        consent_id: 2,
        user_id: 1,
        status: "accepted",
        timestamp: "2026-03-08T00:00:01",
      },
      error: null,
    });
  });

  it("/upload/consent renders with active step 1", async () => {
    setRoute("/upload/consent");
    render(<App />);

    await screen.findByText("USER CONSENT NOTICE");
    const step1 = screen.getByRole("button", { name: "1. Consent" });
    expect(step1).toHaveClass("wizardStep--active");
  });

  it("clicking Next with valid selections routes to /upload/upload", async () => {
    const user = userEvent.setup();
    setRoute("/upload/consent");
    render(<App />);

    await screen.findByText("USER CONSENT NOTICE");

    const yesButtons = screen.getAllByLabelText("Yes, I consent.");
    await user.click(yesButtons[0]);
    await user.click(yesButtons[1]);
    await user.click(screen.getByRole("button", { name: "Next" }));

    await screen.findByText("Upload Placeholder");

    expect(mockedPostInternalConsent).toHaveBeenCalledWith("accepted");
    expect(mockedPostExternalConsent).toHaveBeenCalledWith("accepted");
    expect(window.location.pathname).toBe("/upload/upload");
  });

  it("/upload/upload renders placeholder with active step 2", async () => {
    setRoute("/upload/upload");
    render(<App />);

    await screen.findByText("Upload Placeholder");
    const step2 = screen.getByRole("button", { name: "2. Upload" });
    expect(step2).toHaveClass("wizardStep--active");
  });

  it("sidebar has sticky layout classes", async () => {
    setRoute("/upload/upload");
    const { container } = render(<App />);

    await screen.findByText("Upload Placeholder");
    expect(container.querySelector(".wizardSidebar")).not.toBeNull();
    expect(container.querySelector(".wizardDivider")).not.toBeNull();
  });
});
