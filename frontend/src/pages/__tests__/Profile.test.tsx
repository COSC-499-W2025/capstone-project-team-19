import { describe, it, expect, vi, beforeEach } from "vitest";
import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
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
  changePassword: vi.fn(() => Promise.resolve({ success: true, data: null, error: null })),
  deleteAccount: vi.fn(() => Promise.resolve({ success: true })),
  logout: vi.fn(() => Promise.resolve({ success: true })),
}));

vi.mock("../../auth/token", () => ({
  tokenStore: { get: vi.fn(), set: vi.fn(), clear: vi.fn() },
}));


function renderProfile(initialEntries: string[] = ["/profile"]) {
  const router = createMemoryRouter(
    [
      { path: "/", element: <div data-testid="home-page">home</div> },
      { path: "/projects", element: <div data-testid="projects-page">projects</div> },
      { path: "/profile", element: <ProfilePage /> },
    ],
    { initialEntries }
  );

  return {
    router,
    ...render(<RouterProvider router={router} />),
  };
}

function setup(initialEntries?: string[]) {
  return {
    user: userEvent.setup(),
    ...renderProfile(initialEntries),
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
    expect(screen.getByRole("button", { name: /Change password/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sign out/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Delete account/i })).toBeInTheDocument();
  });

  it("blocks submit when new password and confirm do not match", async () => {
    const { changePassword } = await import("../../api/auth");
    const { user } = setup();

    await screen.findByText("Security");
    await user.click(screen.getByRole("button", { name: /Change password/i }));
    await user.type(screen.getByLabelText("Current password"), "OldPass123");
    await user.type(screen.getByLabelText("New password"), "NewPass123");
    await user.type(screen.getByLabelText("Confirm new password"), "Mismatch123");
    await user.click(screen.getByRole("button", { name: /Save password/i }));

    expect(await screen.findByText("New passwords do not match.")).toBeInTheDocument();
    expect(changePassword).not.toHaveBeenCalled();
  });

  it("blocks submit when current and new password are the same", async () => {
    const { changePassword } = await import("../../api/auth");
    const { user } = setup();

    await screen.findByText("Security");
    await user.click(screen.getByRole("button", { name: /Change password/i }));
    await user.type(screen.getByLabelText("Current password"), "SamePass123");
    await user.type(screen.getByLabelText("New password"), "SamePass123");
    await user.type(screen.getByLabelText("Confirm new password"), "SamePass123");
    await user.click(screen.getByRole("button", { name: /Save password/i }));

    expect(
      await screen.findByText("New password must be different from current password."),
    ).toBeInTheDocument();
    expect(changePassword).not.toHaveBeenCalled();
  });

  it("submits change password and shows success message", async () => {
    const { changePassword } = await import("../../api/auth");
    (changePassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      success: true,
      data: null,
      error: null,
    });

    const { user } = setup();

    await screen.findByText("Security");
    await user.click(screen.getByRole("button", { name: /Change password/i }));
    await user.type(screen.getByLabelText("Current password"), "OldPass123");
    await user.type(screen.getByLabelText("New password"), "NewPass123");
    await user.type(screen.getByLabelText("Confirm new password"), "NewPass123");
    await user.click(screen.getByRole("button", { name: /Save password/i }));

    await vi.waitFor(() => {
      expect(changePassword).toHaveBeenCalledWith("OldPass123", "NewPass123");
    });
    expect(await screen.findByText("Password updated successfully.")).toBeInTheDocument();
  });

  it("shows API error when change password fails", async () => {
    const { changePassword } = await import("../../api/auth");
    (changePassword as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Current password is incorrect"),
    );

    const { user } = setup();

    await screen.findByText("Security");
    await user.click(screen.getByRole("button", { name: /Change password/i }));
    await user.type(screen.getByLabelText("Current password"), "WrongPass123");
    await user.type(screen.getByLabelText("New password"), "NewPass123");
    await user.type(screen.getByLabelText("Confirm new password"), "NewPass123");
    await user.click(screen.getByRole("button", { name: /Save password/i }));

    expect(await screen.findByText("Current password is incorrect")).toBeInTheDocument();
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

    const titleInput = screen.getByPlaceholderText("e.g. BSc in Computer Science");
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

    const roleInput = screen.getByPlaceholderText("e.g. Full Stack Engineer");
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

  it("shows confirmation when Sign out is clicked", async () => {
    const { user } = setup();

    const signOutBtn = await screen.findByRole("button", { name: /^Sign out$/i });
    await user.click(signOutBtn);

    expect(screen.getByText(/Are you sure you want to sign out\?/i)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /^Cancel$/i })[0]).toBeInTheDocument();
    expect(screen.getByTestId("minimal-confirm-button")).toHaveTextContent("Sign out");
  });

  it("shows unsaved-changes dialog when leaving with dirty edits", async () => {
    const { user } = setup();

    const profileTag = await screen.findByText("@testuser");
    const profileCard = profileTag.closest('[data-slot="card"]') as HTMLElement;
    await user.click(within(profileCard).getByRole("button", { name: /Edit/i }));

    const nameInput = screen.getByDisplayValue("Test User");
    await user.clear(nameInput);
    await user.type(nameInput, "Test User Updated");

    await user.click(screen.getByRole("link", { name: /^Projects$/i }));

    expect(
      await screen.findByText(/You have unsaved changes on this page\. Leave without saving\?/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Leave page/i })).toBeInTheDocument();
  });

  it("stays on page when unsaved-changes dialog is canceled", async () => {
    const { user } = setup();

    const profileTag = await screen.findByText("@testuser");
    const profileCard = profileTag.closest('[data-slot="card"]') as HTMLElement;
    await user.click(within(profileCard).getByRole("button", { name: /Edit/i }));

    const nameInput = screen.getByDisplayValue("Test User");
    await user.clear(nameInput);
    await user.type(nameInput, "Test User Updated");

    await user.click(screen.getByRole("link", { name: /^Projects$/i }));
    expect(
      await screen.findByText(/You have unsaved changes on this page\. Leave without saving\?/i)
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^Cancel$/i }));

    expect(
      screen.queryByText(/You have unsaved changes on this page\. Leave without saving\?/i)
    ).not.toBeInTheDocument();
  });

  it("navigates away when unsaved-changes dialog is confirmed", async () => {
    const { user } = setup();

    const profileTag = await screen.findByText("@testuser");
    const profileCard = profileTag.closest('[data-slot="card"]') as HTMLElement;
    await user.click(within(profileCard).getByRole("button", { name: /Edit/i }));

    const nameInput = screen.getByDisplayValue("Test User");
    await user.clear(nameInput);
    await user.type(nameInput, "Test User Updated");

    await user.click(screen.getByRole("link", { name: /^Projects$/i }));
    await user.click(await screen.findByRole("button", { name: /Leave page/i }));

    expect(await screen.findByTestId("projects-page")).toBeInTheDocument();
  });

  it("shows unsaved-changes dialog on browser back navigation", async () => {
    const { user, router } = setup(["/", "/profile"]);

    const profileTag = await screen.findByText("@testuser");
    const profileCard = profileTag.closest('[data-slot="card"]') as HTMLElement;
    await user.click(within(profileCard).getByRole("button", { name: /Edit/i }));

    const nameInput = screen.getByDisplayValue("Test User");
    await user.clear(nameInput);
    await user.type(nameInput, "Test User Updated");

    await act(async () => {
      await router.navigate(-1);
    });

    expect(
      await screen.findByText(/You have unsaved changes on this page\. Leave without saving\?/i)
    ).toBeInTheDocument();
    expect(screen.queryByTestId("home-page")).not.toBeInTheDocument();
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

  it("cancels sign out confirmation", async () => {
    const { logout } = await import("../../api/auth");
    const { user } = setup();

    await user.click(await screen.findByRole("button", { name: /^Sign out$/i }));
    await user.click(screen.getAllByRole("button", { name: /^Cancel$/i })[0]);

    expect(screen.queryByText(/Are you sure you want to sign out\?/i)).not.toBeInTheDocument();
    expect(logout).not.toHaveBeenCalled();
  });

  it("calls logout API, clears token, and redirects to login after confirmation", async () => {
    const { logout } = await import("../../api/auth");
    const { tokenStore } = await import("../../auth/token");

    const replaceFn = vi.fn();
    const originalLocation = window.location;
    Object.defineProperty(window, "location", {
      value: { ...originalLocation, replace: replaceFn },
      writable: true,
    });

    const { user } = setup();
    await user.click(await screen.findByRole("button", { name: /^Sign out$/i }));
    await user.click(screen.getByTestId("minimal-confirm-button"));

    await vi.waitFor(() => {
      expect(logout).toHaveBeenCalled();
    });
    expect(tokenStore.clear).toHaveBeenCalled();
    expect(replaceFn).toHaveBeenCalledWith("/login");

    Object.defineProperty(window, "location", {
      value: originalLocation,
      writable: true,
    });
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
