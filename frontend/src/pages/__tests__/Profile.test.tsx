import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import ProfilePage from "../Profile";

vi.mock("../../auth/user", () => ({
  getUsername: vi.fn(() => "testuser"),
}));

vi.mock("../../components/TopBar", () => ({
  default: () => <div data-testid="topbar" />,
}));

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders without crashing", () => {
    render(<ProfilePage />);
    expect(screen.getByTestId("topbar")).toBeInTheDocument();
  });

  it("displays username and display name from getUsername", () => {
    render(<ProfilePage />);
    expect(screen.getByText("testuser")).toBeInTheDocument();
    expect(screen.getByText(/@testuser/)).toBeInTheDocument();
  });

  it("shows Profile overview section", () => {
    render(<ProfilePage />);
    expect(screen.getByText("Profile overview")).toBeInTheDocument();
    expect(screen.getByText(/Your recent activity and account security controls/)).toBeInTheDocument();
  });

  it("shows stat cards for Uploads, Projects, Resumes", () => {
    render(<ProfilePage />);
    expect(screen.getByText("Uploads")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Resumes")).toBeInTheDocument();
  });

  it("shows Security section with Sign out and Delete account", () => {
    render(<ProfilePage />);
    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(screen.getByText(/Password and account controls/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sign out/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Delete account/i })).toBeInTheDocument();
  });

  it("shows Profile completeness notice", () => {
    render(<ProfilePage />);
    expect(screen.getByText("Profile completeness")).toBeInTheDocument();
    expect(screen.getByText(/UI only for now/)).toBeInTheDocument();
  });
});
