import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "../../App";
import * as consentApi from "../../api/consent";
import { buildConsentSuccessResponses, setAuthenticatedTestUser, setRoute } from "./uploadTestUtils";

vi.mock("../../api/consent", () => ({
  getConsentStatus: vi.fn(),
  postInternalConsent: vi.fn(),
  postExternalConsent: vi.fn(),
}));

const mockedGetConsentStatus = vi.mocked(consentApi.getConsentStatus);
const mockedPostInternalConsent = vi.mocked(consentApi.postInternalConsent);
const mockedPostExternalConsent = vi.mocked(consentApi.postExternalConsent);

describe("upload wizard flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    setAuthenticatedTestUser();

    const defaultResponses = buildConsentSuccessResponses();
    mockedGetConsentStatus.mockResolvedValue(defaultResponses.status);
    mockedPostInternalConsent.mockResolvedValue(defaultResponses.internalSave);
    mockedPostExternalConsent.mockResolvedValue(defaultResponses.externalSave);
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

    await screen.findByText("Only ZIP files are accepted.");

    expect(mockedPostInternalConsent).toHaveBeenCalledWith("accepted");
    expect(mockedPostExternalConsent).toHaveBeenCalledWith("accepted");
    expect(window.location.pathname).toBe("/upload/upload");
  });

  it("shows validation when internal consent is not accepted", async () => {
    const user = userEvent.setup();
    setRoute("/upload/consent");
    render(<App />);

    await screen.findByText("USER CONSENT NOTICE");

    const yesButtons = screen.getAllByLabelText("Yes, I consent.");
    await user.click(yesButtons[1]);
    await user.click(screen.getByRole("button", { name: "Next" }));

    expect(
      await screen.findByText('Please select "Yes, I consent." for user consent to continue.')
    ).toBeInTheDocument();
    expect(mockedPostInternalConsent).not.toHaveBeenCalled();
    expect(mockedPostExternalConsent).not.toHaveBeenCalled();
    expect(window.location.pathname).toBe("/upload/consent");
  });

  it("shows validation when external consent option is missing", async () => {
    const user = userEvent.setup();
    setRoute("/upload/consent");
    render(<App />);

    await screen.findByText("USER CONSENT NOTICE");

    const yesButtons = screen.getAllByLabelText("Yes, I consent.");
    await user.click(yesButtons[0]);
    await user.click(screen.getByRole("button", { name: "Next" }));

    expect(
      await screen.findByText("Please select an external service consent option to continue.")
    ).toBeInTheDocument();
    expect(mockedPostInternalConsent).not.toHaveBeenCalled();
    expect(mockedPostExternalConsent).not.toHaveBeenCalled();
    expect(window.location.pathname).toBe("/upload/consent");
  });

  it("shows save error and stays on consent page when API save fails", async () => {
    const user = userEvent.setup();
    mockedPostExternalConsent.mockResolvedValueOnce({
      success: false,
      data: null,
      error: { message: "Failed external consent save.", code: 500 },
    });

    setRoute("/upload/consent");
    render(<App />);

    await screen.findByText("USER CONSENT NOTICE");

    const yesButtons = screen.getAllByLabelText("Yes, I consent.");
    await user.click(yesButtons[0]);
    await user.click(yesButtons[1]);
    await user.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText("Failed external consent save.")).toBeInTheDocument();
    expect(mockedPostInternalConsent).toHaveBeenCalledWith("accepted");
    expect(mockedPostExternalConsent).toHaveBeenCalledWith("accepted");
    expect(window.location.pathname).toBe("/upload/consent");
  });

  it("/upload/upload renders step 2 with active sidebar state", async () => {
    setRoute("/upload/upload");
    render(<App />);

    await screen.findByText("Only ZIP files are accepted.");
    const step2 = screen.getByRole("button", { name: "2. Upload" });
    expect(step2).toHaveClass("wizardStep--active");
  });

  it("sidebar has sticky layout classes", async () => {
    setRoute("/upload/upload");
    const { container } = render(<App />);

    await screen.findByText("Only ZIP files are accepted.");
    expect(container.querySelector(".wizardSidebar")).not.toBeNull();
    expect(container.querySelector(".wizardDivider")).not.toBeNull();
  });
});
