import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ResumeDetail from "../ResumeDetail";

vi.mock("../../../api/outputs", () => ({
  getResume: vi.fn(),
  editResume: vi.fn(),
  removeProjectFromResume: vi.fn(),
  addProjectToResume: vi.fn(),
  downloadResumeDocx: vi.fn(),
  downloadResumePdf: vi.fn(),
  getResumeProjectEligibleRoles: vi.fn(),
}));

vi.mock("../ExportDropdown", () => ({
  default: () => <button>Export</button>,
}));
vi.mock("../AddProjectModal", () => ({
  default: (props: { onClose: () => void; onAdded: () => void }) => (
    <div data-testid="add-project-modal">
      <button onClick={props.onClose}>Close</button>
      <button
        onClick={() => {
          props.onAdded();
          props.onClose();
        }}
      >
        Add
      </button>
    </div>
  ),
}));

import {
  getResume,
  editResume,
  removeProjectFromResume,
  getResumeProjectEligibleRoles,
} from "../../../api/outputs";

const baseResume = {
  id: 1,
  name: "My Resume",
  created_at: "2026-01-15T00:00:00",
  projects: [
    {
      project_summary_id: 10,
      project_name: "Project Alpha",
      project_type: "code",
      project_mode: "individual",
      languages: ["Python"],
      frameworks: ["FastAPI"],
      summary_text: "A web API project",
      skills: ["OOP", "Testing"],
      text_type: null,
      contribution_percent: null,
      activities: [],
      key_role: "Backend Developer",
      contribution_bullets: ["Built REST API", "Wrote tests"],
      start_date: null,
      end_date: null,
    },
  ],
  aggregated_skills: {
    languages: ["Python"],
    frameworks: ["FastAPI"],
    technical_skills: ["OOP"],
    writing_skills: [],
  },
  rendered_text: null,
};

function setupMocks(overrides: Partial<typeof baseResume> = {}) {
  const resume = { ...baseResume, ...overrides };
  vi.mocked(getResume).mockResolvedValue({
    success: true,
    data: resume,
    error: null,
  } as any);
  vi.mocked(getResumeProjectEligibleRoles).mockResolvedValue({
    success: true,
    data: { roles: ["Backend Developer", "Frontend Developer", "Full-Stack Developer"] },
    error: null,
  } as any);
  return resume;
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("ResumeDetail", () => {
  describe("view mode (default)", () => {
    it("renders resume name and project content", async () => {
      setupMocks();
      render(<ResumeDetail resumeId={1} onBack={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("My Resume")).toBeInTheDocument();
      });
      expect(screen.getByText("Project Alpha")).toBeInTheDocument();
      expect(screen.getByText(/Backend Developer/)).toBeInTheDocument();
      expect(screen.getByText(/Built REST API/)).toBeInTheDocument();
    });

    it("shows Edit button in header", async () => {
      setupMocks();
      render(<ResumeDetail resumeId={1} onBack={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("Edit")).toBeInTheDocument();
      });
    });

    it("does not show pencil icons in view mode", async () => {
      setupMocks();
      render(<ResumeDetail resumeId={1} onBack={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("My Resume")).toBeInTheDocument();
      });
      expect(screen.queryByLabelText("Display Name")).not.toBeInTheDocument();
    });

    it("shows loading state", () => {
      vi.mocked(getResume).mockReturnValue(new Promise(() => {}));
      render(<ResumeDetail resumeId={1} onBack={vi.fn()} />);
      expect(screen.getByText("Loading...")).toBeInTheDocument();
    });

    it("shows error state", async () => {
      vi.mocked(getResume).mockRejectedValue(new Error("Network error"));
      render(<ResumeDetail resumeId={1} onBack={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
    });

    it("calls onBack when back button clicked", async () => {
      setupMocks();
      const onBack = vi.fn();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} onBack={onBack} />);

      await waitFor(() => screen.getByText("My Resume"));
      const buttons = screen.getAllByRole("button");
      const backBtn = buttons.find(
        (b) => b.querySelector("svg") && !b.textContent?.trim()
      );
      expect(backBtn).toBeDefined();
      await user.click(backBtn!);
      expect(onBack).toHaveBeenCalled();
    });

    it("shows skills summary", async () => {
      setupMocks();
      render(<ResumeDetail resumeId={1} onBack={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("Skills")).toBeInTheDocument();
      });
      expect(screen.getAllByText(/Python/).length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("toggling edit mode", () => {
    it("clicking Edit switches to edit mode with Done Editing button", async () => {
      setupMocks();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Edit"));
      await user.click(screen.getByText("Edit"));

      expect(screen.getByText("Done Editing")).toBeInTheDocument();
      expect(screen.queryByText("Edit")).not.toBeInTheDocument();
    });

    it("clicking Done Editing returns to view mode", async () => {
      setupMocks();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Edit"));
      await user.click(screen.getByText("Edit"));
      await user.click(screen.getByText("Done Editing"));

      expect(screen.getByText("Edit")).toBeInTheDocument();
      expect(screen.queryByText("Done Editing")).not.toBeInTheDocument();
    });

    it("starts in edit mode when initialEditing is true", async () => {
      setupMocks();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("Done Editing")).toBeInTheDocument();
      });
    });
  });

  describe("editing resume name", () => {
    it("shows name pencil icon only in edit mode", async () => {
      setupMocks();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("My Resume"));
      expect(screen.getByText("Done Editing")).toBeInTheDocument();
    });

    it("saves resume name on confirm", async () => {
      setupMocks();
      vi.mocked(editResume).mockResolvedValue({
        success: true,
        data: { ...baseResume, name: "Updated Name" },
        error: null,
      } as any);

      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("My Resume"));

      const buttons = screen.getAllByRole("button");
      const pencilBtn = buttons.find(
        (b) => b.querySelector("svg") && b.closest("h2")
      );
      if (pencilBtn) {
        await user.click(pencilBtn);

        const input = screen.getByDisplayValue("My Resume");
        await user.clear(input);
        await user.type(input, "Updated Name");

        const checkBtns = screen.getAllByRole("button");
        const checkBtn = checkBtns.find(
          (b) => b.querySelector(".text-emerald-600") !== null
        );
        if (checkBtn) await user.click(checkBtn);

        await waitFor(() => {
          expect(editResume).toHaveBeenCalledWith(1, { name: "Updated Name" });
        });
      }
    });
  });

  describe("editing project fields", () => {
    it("shows edit form when project pencil is clicked", async () => {
      setupMocks();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));

      const buttons = screen.getAllByRole("button");
      const projectPencil = buttons.find(
        (b) => b.querySelector("svg") && !b.closest("h2") && b.closest("[data-slot='card-action']")
      );
      if (projectPencil) {
        await user.click(projectPencil);

        await waitFor(() => {
          expect(screen.getByLabelText("Display Name")).toBeInTheDocument();
          expect(screen.getByLabelText("Key Role")).toBeInTheDocument();
          expect(screen.getByLabelText("Summary")).toBeInTheDocument();
          expect(screen.getByText("Save changes")).toBeInTheDocument();
          expect(screen.getByText("Cancel")).toBeInTheDocument();
        });
      }
    });

    it("loads eligible roles into key role dropdown when project edit opens", async () => {
      setupMocks();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));

      const buttons = screen.getAllByRole("button");
      const projectPencil = buttons.find(
        (b) => b.querySelector("svg") && !b.closest("h2") && b.closest("[data-slot='card-action']")
      );
      if (projectPencil) {
        await user.click(projectPencil);

        await waitFor(() => {
          const roleSelect = screen.getByLabelText("Key Role");
          expect(roleSelect).toBeInTheDocument();
          expect(screen.getByRole("option", { name: "Backend Developer" })).toBeInTheDocument();
          expect(screen.getByRole("option", { name: "Frontend Developer" })).toBeInTheDocument();
          expect(screen.getByRole("option", { name: "Full-Stack Developer" })).toBeInTheDocument();
        });

        expect(getResumeProjectEligibleRoles).toHaveBeenCalledWith(1, 10);
      }
    });

    it("shows loading state in key role dropdown while roles are fetching", async () => {
      setupMocks();
      vi.mocked(getResumeProjectEligibleRoles).mockReturnValue(new Promise(() => {}));

      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));

      const buttons = screen.getAllByRole("button");
      const projectPencil = buttons.find(
        (b) => b.querySelector("svg") && !b.closest("h2") && b.closest("[data-slot='card-action']")
      );
      if (projectPencil) {
        await user.click(projectPencil);
        await waitFor(() => {
          expect(screen.getByRole("option", { name: "Loading roles..." })).toBeInTheDocument();
        });
      }
    });

    it("cancels project edit without saving", async () => {
      setupMocks();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));

      const buttons = screen.getAllByRole("button");
      const projectPencil = buttons.find(
        (b) => b.querySelector("svg") && !b.closest("h2") && b.closest("[data-slot='card-action']")
      );
      if (projectPencil) {
        await user.click(projectPencil);
        await waitFor(() => screen.getByText("Cancel"));
        await user.click(screen.getByText("Cancel"));

        expect(screen.queryByLabelText("Display Name")).not.toBeInTheDocument();
        expect(editResume).not.toHaveBeenCalled();
      }
    });

    it("saves project edits and shows success message", async () => {
      setupMocks();
      vi.mocked(editResume).mockResolvedValue({
        success: true,
        data: baseResume,
        error: null,
      } as any);

      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));

      const buttons = screen.getAllByRole("button");
      const projectPencil = buttons.find(
        (b) => b.querySelector("svg") && !b.closest("h2") && b.closest("[data-slot='card-action']")
      );
      if (projectPencil) {
        await user.click(projectPencil);
        await waitFor(() => screen.getByLabelText("Display Name"));

        const nameInput = screen.getByLabelText("Display Name");
        await user.clear(nameInput);
        await user.type(nameInput, "Renamed Project");

        await user.click(screen.getByText("Save changes"));

        await waitFor(() => {
          expect(editResume).toHaveBeenCalledWith(
            1,
            expect.objectContaining({
              project_summary_id: 10,
              scope: "resume_only",
              display_name: "Renamed Project",
            })
          );
        });

        await waitFor(() => {
          expect(screen.getByText("Updated this resume")).toBeInTheDocument();
        });
      }
    });

    it("shows global success message when scope is global", async () => {
      setupMocks();
      vi.mocked(editResume).mockResolvedValue({
        success: true,
        data: baseResume,
        error: null,
      } as any);

      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));

      const buttons = screen.getAllByRole("button");
      const projectPencil = buttons.find(
        (b) => b.querySelector("svg") && !b.closest("h2") && b.closest("[data-slot='card-action']")
      );
      if (projectPencil) {
        await user.click(projectPencil);

        await waitFor(() => screen.getByLabelText("Key Role"));

        const roleSelect = screen.getByLabelText("Key Role");
        await user.selectOptions(roleSelect, "Full-Stack Developer");

        await user.click(screen.getByLabelText("All resumes & portfolio"));
        await user.click(screen.getByText("Save changes"));

        await waitFor(() => {
          expect(editResume).toHaveBeenCalledWith(
            1,
            expect.objectContaining({
              scope: "global",
              key_role: "Full-Stack Developer",
            })
          );
        });

        await waitFor(() => {
          expect(screen.getByText("Updated across all resumes")).toBeInTheDocument();
        });
      }
    });

    it("does not call API if no fields changed", async () => {
      setupMocks();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));

      const buttons = screen.getAllByRole("button");
      const projectPencil = buttons.find(
        (b) => b.querySelector("svg") && !b.closest("h2") && b.closest("[data-slot='card-action']")
      );
      if (projectPencil) {
        await user.click(projectPencil);
        await waitFor(() => screen.getByText("Save changes"));

        await user.click(screen.getByText("Save changes"));

        expect(editResume).not.toHaveBeenCalled();
      }
    });
  });

  describe("remove project from resume", () => {
    it("shows remove button on project card in edit mode", async () => {
      setupMocks();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));

      const removeBtns = screen.getAllByRole("button", { name: "Remove from resume" });
      expect(removeBtns.length).toBeGreaterThanOrEqual(1);
    });

    it("opens confirmation dialog when remove button is clicked", async () => {
      setupMocks({
        projects: [
          baseResume.projects[0],
          {
            ...baseResume.projects[0],
            project_summary_id: 11,
            project_name: "Project Beta",
          },
        ],
      });
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));
      const removeBtns = screen.getAllByRole("button", { name: "Remove from resume" });
      await user.click(removeBtns[0]);

      await waitFor(() => {
        expect(
          screen.getByText(/Remove "Project Alpha" from this resume\?/)
        ).toBeInTheDocument();
      });
      expect(screen.getByText("Cancel")).toBeInTheDocument();
      expect(screen.getByText("Remove")).toBeInTheDocument();
    });

    it("closes dialog and does not call API when Cancel is clicked", async () => {
      setupMocks({
        projects: [
          baseResume.projects[0],
          {
            ...baseResume.projects[0],
            project_summary_id: 11,
            project_name: "Project Beta",
          },
        ],
      });
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));
      const removeBtns = screen.getAllByRole("button", { name: "Remove from resume" });
      await user.click(removeBtns[0]);
      await waitFor(() => screen.getByText(/Remove "Project Alpha"/));
      await user.click(screen.getByText("Cancel"));

      expect(removeProjectFromResume).not.toHaveBeenCalled();
      expect(screen.queryByText(/Remove "Project Alpha"/)).not.toBeInTheDocument();
    });

    it("calls removeProjectFromResume and updates resume on success", async () => {
      setupMocks();
      const resumeWithoutProject = {
        ...baseResume,
        projects: [],
        aggregated_skills: { languages: [], frameworks: [], technical_skills: [], writing_skills: [] },
      };
      vi.mocked(removeProjectFromResume).mockResolvedValue({
        success: true,
        data: resumeWithoutProject,
        error: null,
      } as any);

      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));
      const removeBtns = screen.getAllByRole("button", { name: "Remove from resume" });
      await user.click(removeBtns[0]);
      const confirmBtn = await screen.findByTestId("minimal-confirm-button");
      await user.click(confirmBtn);

      await waitFor(() => {
        expect(removeProjectFromResume).toHaveBeenCalledWith(1, "Project Alpha");
      });

      await waitFor(() => {
        expect(screen.getByText("Project removed from resume")).toBeInTheDocument();
      });
    });

    it("calls onBack when resume is deleted (last project removed)", async () => {
      setupMocks();
      vi.mocked(removeProjectFromResume).mockResolvedValue({
        success: true,
        data: null,
        error: null,
      } as any);

      const onBack = vi.fn();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={onBack} />);

      await waitFor(() => screen.getByText("Project Alpha"));
      const removeBtns = screen.getAllByRole("button", { name: "Remove from resume" });
      await user.click(removeBtns[0]);
      const confirmBtn = await screen.findByTestId("minimal-confirm-button");
      await user.click(confirmBtn);

      await waitFor(() => {
        expect(removeProjectFromResume).toHaveBeenCalledWith(1, "Project Alpha");
        expect(onBack).toHaveBeenCalled();
      });
    });

    it("hides Export when editing", async () => {
      setupMocks();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} onBack={vi.fn()} />);
      await waitFor(() => screen.getByText("Edit"));
      expect(screen.getByText("Export")).toBeInTheDocument();
      await user.click(screen.getByText("Edit"));
      expect(screen.queryByText("Export")).not.toBeInTheDocument();
    });

    it("shows Add Project button in edit mode and opens modal on click", async () => {
      setupMocks();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);
      await waitFor(() => screen.getByText("Add Project"));
      expect(screen.queryByTestId("add-project-modal")).not.toBeInTheDocument();
      await user.click(screen.getByText("Add Project"));
      expect(screen.getByTestId("add-project-modal")).toBeInTheDocument();
    });

    it("adds project via modal and shows success message", async () => {
      setupMocks();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);
      await waitFor(() => screen.getByText("Add Project"));
      await user.click(screen.getByText("Add Project"));
      await user.click(screen.getByText("Add"));
      await waitFor(() => {
        expect(screen.getByText("Project added to resume")).toBeInTheDocument();
      });
    });

    it("shows error when remove fails", async () => {
      vi.mocked(removeProjectFromResume).mockRejectedValue(
        new Error("Failed to remove project")
      );

      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));
      const removeBtns = screen.getAllByRole("button", { name: "Remove from resume" });
      await user.click(removeBtns[0]);
      const confirmBtn = await screen.findByTestId("minimal-confirm-button");
      await user.click(confirmBtn);

      await waitFor(() => {
        expect(screen.getByText("Failed to remove project")).toBeInTheDocument();
      });
    });
  });

  describe("leaving edit mode cleans up", () => {
    it("collapses open project edit when Done Editing is clicked", async () => {
      setupMocks();
      const user = userEvent.setup();
      render(<ResumeDetail resumeId={1} initialEditing onBack={vi.fn()} />);

      await waitFor(() => screen.getByText("Project Alpha"));

      const buttons = screen.getAllByRole("button");
      const projectPencil = buttons.find(
        (b) => b.querySelector("svg") && !b.closest("h2") && b.closest("[data-slot='card-action']")
      );
      if (projectPencil) {
        await user.click(projectPencil);
        await waitFor(() => screen.getByLabelText("Display Name"));

        await user.click(screen.getByText("Done Editing"));

        expect(screen.queryByLabelText("Display Name")).not.toBeInTheDocument();
        expect(screen.getByText("Edit")).toBeInTheDocument();
      }
    });
  });
});