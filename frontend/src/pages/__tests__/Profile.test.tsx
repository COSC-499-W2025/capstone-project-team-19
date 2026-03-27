import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ProfilePage from "../Profile";

vi.mock("../../auth/user", () => ({
  getUsername: vi.fn(() => "testuser"),
}));

vi.mock("../../components/TopBar", () => ({
  default: () => <div data-testid="topbar" />,
}));

vi.mock("../../api/portfolioSettings", () => ({
  getPortfolioSettings: vi.fn(() =>
    Promise.resolve({
      portfolio_public: false,
      active_resume_id: null,
    })
  ),
  updatePortfolioSettings: vi.fn(),
}));

vi.mock("../../api/outputs", () => ({
  listResumes: vi.fn(() =>
    Promise.resolve({
      success: true,
      data: { resumes: [] },
      error: null,
    })
  ),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <ProfilePage />
    </MemoryRouter>
  );
}

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders without crashing", () => {
    renderPage();
    expect(screen.getByTestId("topbar")).toBeInTheDocument();
  });

  it("displays username and display name from getUsername", () => {
    renderPage();
    expect(screen.getByText("testuser")).toBeInTheDocument();
    expect(screen.getByText(/@testuser/)).toBeInTheDocument();
  });

  it("shows Profile overview section", () => {
    renderPage();
    expect(screen.getByText("Profile overview")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Your account activity, personal information and security controls\./
      )
    ).toBeInTheDocument();
  });

  it("shows stat cards for Uploads, Projects, Resumes", () => {
    renderPage();
    expect(screen.getByText("Uploads")).toBeInTheDocument();
    expect(screen.getAllByText("Projects").length).toBeGreaterThan(0);
    expect(screen.getByText("Resumes")).toBeInTheDocument();
  });

  it("shows Security section with Sign out and Delete account", () => {
    renderPage();
    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(
      screen.getByText(/Password and account controls/)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Sign out/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Delete account/i })
    ).toBeInTheDocument();
  });

  it("shows Profile completeness notice", () => {
    renderPage();
    expect(screen.getByText("Profile completeness")).toBeInTheDocument();
    expect(screen.getByText(/UI only for now/)).toBeInTheDocument();
  });
});