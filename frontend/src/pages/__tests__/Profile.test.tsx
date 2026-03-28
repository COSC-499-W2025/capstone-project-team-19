import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
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
      profile_text: "Existing summary",
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
      profile_text: p.profile_text ?? "Existing summary",
    }),
  ),
  getEducation: vi.fn(() => Promise.resolve({ entries: [] })),
  replaceEducation: vi.fn((payload: { entries: Array<{ title: string; organization?: string | null; date_text?: string | null; description?: string | null }> }) =>
    Promise.resolve({
      entries: payload.entries.map((e, idx: number) => ({
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
  getCertifications: vi.fn(() => Promise.resolve({ entries: [] })),
  replaceCertifications: vi.fn((payload: { entries: Array<{ title: string; organization?: string | null; date_text?: string | null; description?: string | null }> }) =>
    Promise.resolve({
      entries: payload.entries.map((e, idx: number) => ({
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
  getExperience: vi.fn(() => Promise.resolve({ entries: [] })),
  replaceExperience: vi.fn((payload: { entries: Array<{ role: string; company?: string | null; date_text?: string | null; description?: string | null }> }) =>
    Promise.resolve({
      entries: payload.entries.map((e, idx: number) => ({
        entry_id: idx + 1,
        role: e.role,
        company: e.company ?? null,
        date_text: e.date_text ?? null,
        description: e.description ?? null,
        display_order: idx + 1,
        created_at: null,
        updated_at: null,
      })),
    }),
  ),
}));

vi.mock("../../api/portfolioSettings", () => ({
  getPortfolioSettings: vi.fn(() =>
    Promise.resolve({
      portfolio_public: false,
      active_resume_id: null,
    }),
  ),
  updatePortfolioSettings: vi.fn((settings) =>
    Promise.resolve({
      portfolio_public:
        typeof settings.portfolio_public === "boolean"
          ? settings.portfolio_public
          : false,
      active_resume_id:
        typeof settings.active_resume_id === "number"
          ? settings.active_resume_id
          : null,
    }),
  ),
}));

vi.mock("../../api/outputs", () => ({
  listResumes: vi.fn(() =>
    Promise.resolve({
      success: true,
      data: { resumes: [{ id: 1, name: "Resume 1", created_at: null }] },
      error: null,
    }),
  ),
}));

vi.mock("../../api/auth", () => ({
  deleteAccount: vi.fn(() => Promise.resolve({ success: true })),
}));

vi.mock("../../auth/token", () => ({
  tokenStore: { get: vi.fn(), set: vi.fn(), clear: vi.fn() },
}));


function renderProfile() {
  return render(
    <MemoryRouter>
      <ProfilePage />
    </MemoryRouter>
  );
}

function setup() {
  return {
    user: userEvent.setup(),
    ...renderProfile(),
  };
}

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders top bar and username tag", async () => {
    renderProfile();
    expect(screen.getByTestId("topbar")).toBeInTheDocument();
    expect(await screen.findByText("@testuser")).toBeInTheDocument();
  });

  it("shows Profile overview and all main sections", async () => {
    renderProfile();
    expect(await screen.findByText("Profile overview")).toBeInTheDocument();
    expect(screen.getByText("Profile summary")).toBeInTheDocument();
    expect(screen.getByText("Education")).toBeInTheDocument();
    expect(screen.getByText("Experience")).toBeInTheDocument();
    expect(screen.getByText("Certifications")).toBeInTheDocument();
    expect(screen.getByText("Public Portfolio")).toBeInTheDocument();
  });

  it("shows Security section with Sign out and Delete account", async () => {
    renderProfile();
    expect(await screen.findByText("Security")).toBeInTheDocument();
    expect(screen.getByText(/Password and account controls/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sign out/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Delete account/i })).toBeInTheDocument();
  });

  it("renders existing profile summary text", async () => {
    renderProfile();
    expect(await screen.findByText("Existing summary")).toBeInTheDocument();
  });

  it("allows editing certifications and shows saved title", async () => {
    const { user } = setup();

    const certTitle = await screen.findByText("Certifications");
    const certCard = certTitle.closest('[data-slot="card"]') as HTMLElement;
    const editButton = within(certCard).getByRole("button", { name: /Edit/i });
    await user.click(editButton);

    const titleInput = screen.getByPlaceholderText("BSc in Computer Science");
    await user.clear(titleInput);
    await user.type(titleInput, "AWS Cloud Practitioner");

    const saveButton = within(certCard).getByRole("button", { name: /Save/i });
    await user.click(saveButton);

    expect(await screen.findByText("AWS Cloud Practitioner")).toBeInTheDocument();
  });

  it("allows editing experience and shows saved role", async () => {
    const { user } = setup();

    const expTitle = await screen.findByText("Experience");
    const expCard = expTitle.closest('[data-slot="card"]') as HTMLElement;
    const editButton = within(expCard).getByRole("button", { name: /Edit/i });
    await user.click(editButton);

    const roleInput = screen.getByPlaceholderText("Full Stack Engineer");
    await user.clear(roleInput);
    await user.type(roleInput, "Backend Developer");

    const saveButton = within(expCard).getByRole("button", { name: /Save/i });
    await user.click(saveButton);

    expect(await screen.findByText("Backend Developer")).toBeInTheDocument();
  });

  it("toggles public portfolio visibility label", async () => {
    const { user } = setup();

    const visibilityButton = await screen.findByRole("button", { name: /Private/i });
    await user.click(visibilityButton);

    expect(await screen.findByRole("button", { name: /Public/i })).toBeInTheDocument();
  });

  it("shows confirmation when Delete account is clicked", async () => {
    const { user } = setup();

    const deleteBtn = await screen.findByRole("button", { name: /Delete account/i });
    await user.click(deleteBtn);

    expect(screen.getByText(/permanently delete your account/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Yes, delete my account/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Cancel/i })).toBeInTheDocument();
  });

  it("cancels delete account confirmation", async () => {
    const { user } = setup();

    const deleteBtn = await screen.findByRole("button", { name: /Delete account/i });
    await user.click(deleteBtn);

    await user.click(screen.getByRole("button", { name: /Cancel/i }));

    // Confirmation gone, original button back
    expect(screen.queryByText(/permanently delete your account/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Delete account/i })).toBeInTheDocument();
  });

  it("calls deleteAccount API, clears token, and redirects to login", async () => {
    const { deleteAccount } = await import("../../api/auth");
    const { tokenStore } = await import("../../auth/token");

    const replaceFn = vi.fn();
    const originalLocation = window.location;
    Object.defineProperty(window, "location", {
      value: { ...originalLocation, replace: replaceFn },
      writable: true,
    });

    const { user } = setup();

    const deleteBtn = await screen.findByRole("button", { name: /Delete account/i });
    await user.click(deleteBtn);

    await user.click(screen.getByRole("button", { name: /Yes, delete my account/i }));

    await vi.waitFor(() => {
      expect(deleteAccount).toHaveBeenCalled();
    });
    expect(tokenStore.clear).toHaveBeenCalled();
    expect(replaceFn).toHaveBeenCalledWith("/login");

    Object.defineProperty(window, "location", {
      value: originalLocation,
      writable: true,
    });
  });
});