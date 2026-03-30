import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CreateResumeModal from "../CreateResumeModal";

vi.mock("../../../api/outputs", () => ({
  getRankedProjects: vi.fn(),
  createResume: vi.fn(),
}));

import { getRankedProjects, createResume } from "../../../api/outputs";

const sampleProjects = [
  { rank: 1, project_summary_id: 10, project_name: "Project Alpha", score: 0.85, manual_rank: null },
  { rank: 2, project_summary_id: 20, project_name: "Project Beta", score: 0.72, manual_rank: null },
];

function mockProjects(projects = sampleProjects) {
  vi.mocked(getRankedProjects).mockResolvedValue({
    success: true,
    data: { rankings: projects },
    error: null,
  } as any);
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("CreateResumeModal", () => {
  it("loads and displays available projects", async () => {
    mockProjects();
    render(<CreateResumeModal onClose={vi.fn()} onCreated={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Project Alpha")).toBeInTheDocument();
    });
    expect(screen.getByText("Project Beta")).toBeInTheDocument();
    expect(screen.getByText("0.85")).toBeInTheDocument();
    expect(screen.getByText("0.72")).toBeInTheDocument();
  });

  it("shows loading state while fetching projects", () => {
    vi.mocked(getRankedProjects).mockReturnValue(new Promise(() => {}));
    render(<CreateResumeModal onClose={vi.fn()} onCreated={vi.fn()} />);

    expect(screen.getByText("Loading projects...")).toBeInTheDocument();
  });

  it("shows empty state when no projects exist", async () => {
    mockProjects([]);
    render(<CreateResumeModal onClose={vi.fn()} onCreated={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("No projects found. Upload a project first.")).toBeInTheDocument();
    });
  });

  it("shows error when project fetch fails", async () => {
    vi.mocked(getRankedProjects).mockRejectedValue(new Error("Fetch failed"));
    render(<CreateResumeModal onClose={vi.fn()} onCreated={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Fetch failed")).toBeInTheDocument();
    });
  });

  it("has default title of 'My Resume'", async () => {
    mockProjects();
    render(<CreateResumeModal onClose={vi.fn()} onCreated={vi.fn()} />);

    await waitFor(() => screen.getByText("Project Alpha"));
    expect(screen.getByDisplayValue("My Resume")).toBeInTheDocument();
  });

  it("allows editing the title", async () => {
    mockProjects();
    const user = userEvent.setup();
    render(<CreateResumeModal onClose={vi.fn()} onCreated={vi.fn()} />);

    await waitFor(() => screen.getByText("Project Alpha"));
    const input = screen.getByDisplayValue("My Resume");
    await user.clear(input);
    await user.type(input, "Custom Title");

    expect(screen.getByDisplayValue("Custom Title")).toBeInTheDocument();
  });

  it("shows error when trying to create with no projects selected", async () => {
    mockProjects();
    const user = userEvent.setup();
    render(<CreateResumeModal onClose={vi.fn()} onCreated={vi.fn()} />);

    await waitFor(() => screen.getByText("Project Alpha"));
    await user.click(screen.getByText("Create Resume"));

    expect(screen.getByText("Select at least one project.")).toBeInTheDocument();
    expect(createResume).not.toHaveBeenCalled();
  });

  it("creates resume with selected projects and calls onCreated", async () => {
    mockProjects();
    vi.mocked(createResume).mockResolvedValue({
      success: true,
      data: { id: 5, name: "My Resume", created_at: null, projects: [], aggregated_skills: { languages: [], frameworks: [], technical_skills: [], writing_skills: [] }, rendered_text: null },
      error: null,
    } as any);

    const onCreated = vi.fn();
    const user = userEvent.setup();
    render(<CreateResumeModal onClose={vi.fn()} onCreated={onCreated} />);

    await waitFor(() => screen.getByText("Project Alpha"));

    // Click the row to select (row onClick toggles)
    await user.click(screen.getByText("Project Alpha"));

    await user.click(screen.getByText("Create Resume"));

    await waitFor(() => {
      expect(createResume).toHaveBeenCalledWith("My Resume", [10]);
    });
    expect(onCreated).toHaveBeenCalledWith(5);
  });

  it("creates resume with multiple selected projects", async () => {
    mockProjects();
    vi.mocked(createResume).mockResolvedValue({
      success: true,
      data: { id: 6, name: "My Resume", created_at: null, projects: [], aggregated_skills: { languages: [], frameworks: [], technical_skills: [], writing_skills: [] }, rendered_text: null },
      error: null,
    } as any);

    const onCreated = vi.fn();
    const user = userEvent.setup();
    render(<CreateResumeModal onClose={vi.fn()} onCreated={onCreated} />);

    await waitFor(() => screen.getByText("Project Alpha"));

    // Click rows to select
    await user.click(screen.getByText("Project Alpha"));
    await user.click(screen.getByText("Project Beta"));

    await user.click(screen.getByText("Create Resume"));

    await waitFor(() => {
      expect(createResume).toHaveBeenCalledWith("My Resume", expect.arrayContaining([10, 20]));
    });
  });

  it("can deselect a project by clicking row again", async () => {
    mockProjects();
    const user = userEvent.setup();
    render(<CreateResumeModal onClose={vi.fn()} onCreated={vi.fn()} />);

    await waitFor(() => screen.getByText("Project Alpha"));

    await user.click(screen.getByText("Project Alpha")); // select
    await user.click(screen.getByText("Project Alpha")); // deselect

    await user.click(screen.getByText("Create Resume"));
    expect(screen.getByText("Select at least one project.")).toBeInTheDocument();
  });

  it("shows error when create API fails", async () => {
    mockProjects();
    vi.mocked(createResume).mockRejectedValue(new Error("Creation failed"));

    const user = userEvent.setup();
    render(<CreateResumeModal onClose={vi.fn()} onCreated={vi.fn()} />);

    await waitFor(() => screen.getByText("Project Alpha"));

    await user.click(screen.getByText("Project Alpha"));
    await user.click(screen.getByText("Create Resume"));

    await waitFor(() => {
      expect(screen.getByText("Creation failed")).toBeInTheDocument();
    });
  });

  it("calls onClose when close button is clicked", async () => {
    mockProjects();
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<CreateResumeModal onClose={onClose} onCreated={vi.fn()} />);

    await waitFor(() => screen.getByText("Project Alpha"));
    // Close button is now an icon button with X SVG
    const buttons = screen.getAllByRole("button");
    const closeBtn = buttons.find(
      (b) => b.querySelector("svg") && b.className.includes("absolute")
    );
    expect(closeBtn).toBeDefined();
    await user.click(closeBtn!);
    expect(onClose).toHaveBeenCalled();
  });

  it("disables Create button while creating", async () => {
    mockProjects();
    // Never resolve so we stay in creating state
    vi.mocked(createResume).mockReturnValue(new Promise(() => {}));

    const user = userEvent.setup();
    render(<CreateResumeModal onClose={vi.fn()} onCreated={vi.fn()} />);

    await waitFor(() => screen.getByText("Project Alpha"));

    await user.click(screen.getByText("Project Alpha"));
    await user.click(screen.getByText("Create Resume"));

    expect(screen.getByText("Creating...")).toBeInTheDocument();
    expect(screen.getByText("Creating...").closest("button")).toBeDisabled();
  });
});
