import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import ProfilePage from "../Profile";

vi.mock("../../auth/user", () => ({
  getUsername: vi.fn(() => "testuser"),
}));

vi.mock("../../components/TopBar", () => ({
  default: () => <div data-testid="topbar" />,
}));

vi.mock("../../api/profile", () => ({
  getProfile: vi.fn(() =>
    Promise.resolve({
      user_id: 1,
      email: "user@example.com",
      full_name: "Test User",
      phone: null,
      linkedin: null,
      github: null,
      location: null,
      profile_text: null,
    }),
  ),
  updateProfile: vi.fn((p) =>
    Promise.resolve({
      user_id: 1,
      email: p.email ?? "user@example.com",
      full_name: p.full_name ?? "Test User",
      phone: p.phone ?? null,
      linkedin: p.linkedin ?? null,
      github: p.github ?? null,
      location: p.location ?? null,
      profile_text: p.profile_text ?? null,
    }),
  ),
  getEducation: vi.fn(() =>
    Promise.resolve({
      entries: [],
    }),
  ),
  replaceEducation: vi.fn((payload) =>
    Promise.resolve({
      entries: payload.entries.map((e, idx) => ({
        entry_id: idx + 1,
        entry_type: "education",
        title: e.title,
        organization: e.organization ?? null,
        date_text: e.date_text ?? null,
        description: e.description ?? null,
        display_order: idx + 1,
        created_at: null,
        updated_at: null,
      })),
    }),
  ),
  getCertifications: vi.fn(() =>
    Promise.resolve({
      entries: [],
    }),
  ),
  replaceCertifications: vi.fn((payload) =>
    Promise.resolve({
      entries: payload.entries.map((e, idx) => ({
        entry_id: idx + 1,
        entry_type: "certificate",
        title: e.title,
        organization: e.organization ?? null,
        date_text: e.date_text ?? null,
        description: e.description ?? null,
        display_order: idx + 1,
        created_at: null,
        updated_at: null,
      })),
    }),
  ),
}));

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders without crashing", async () => {
    render(<ProfilePage />);
    expect(screen.getByTestId("topbar")).toBeInTheDocument();
    expect(await screen.findByText("Profile details")).toBeInTheDocument();
  });

  it("displays username and display name from getUsername", async () => {
    render(<ProfilePage />);
    expect(await screen.findByText("testuser")).toBeInTheDocument();
    expect(screen.getByText(/@testuser/)).toBeInTheDocument();
  });

  it("shows Profile overview and sections", async () => {
    render(<ProfilePage />);
    expect(await screen.findByText("Profile overview")).toBeInTheDocument();
    expect(screen.getByText("Profile details")).toBeInTheDocument();
    expect(screen.getByText("Education")).toBeInTheDocument();
    expect(screen.getByText("Certifications")).toBeInTheDocument();
  });

  it("shows Security section with Sign out and Delete account", async () => {
    render(<ProfilePage />);
    expect(await screen.findByText("Security")).toBeInTheDocument();
    expect(screen.getByText(/Password and account controls/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sign out/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Delete account/i })).toBeInTheDocument();
  });
});

