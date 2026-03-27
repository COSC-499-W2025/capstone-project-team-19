import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import ProjectDetailPage from "../ProjectDetail";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>(
    "react-router-dom"
  );

  return {
    ...actual,
    useNavigate: vi.fn(() => mockNavigate),
    useParams: vi.fn(() => ({ id: "42" })),
  };
});

vi.mock("../../api/projects", () => ({
  getProject: vi.fn(),
  fetchThumbnailUrl: vi.fn(),
  getProjectDates: vi.fn(),
  getProjectFeedback: vi.fn(),
  listProjects: vi.fn(),
  uploadThumbnail: vi.fn(),
  deleteThumbnail: vi.fn(),
  deleteProject: vi.fn(),
  patchProjectDates: vi.fn(),
  resetProjectDates: vi.fn(),
}));

vi.mock("../../auth/user", () => ({
  getUsername: vi.fn(() => "testuser"),
}));

vi.mock("../../components/TopBar", () => ({
  default: () => <div data-testid="topbar" />,
}));

import {
  getProject,
  fetchThumbnailUrl,
  getProjectDates,
  getProjectFeedback,
  listProjects,
  deleteProject,
  patchProjectDates,
  resetProjectDates,
  deleteThumbnail,
} from "../../api/projects";

const baseProject = {
  project_summary_id: 42,
  project_key: null,
  project_name: "Test Project",
  project_type: "personal",
  project_mode: "solo",
  created_at: null,
  summary_text: "A test project summary.",
  languages: ["TypeScript"],
  frameworks: ["React"],
  skills: ["frontend"],
  contributions: {},
};

const baseDates = {
  project_summary_id: 42,
  project_name: "Test Project",
  start_date: "2024-01-01",
  end_date: "2024-06-01",
  source: "AUTO" as const,
  manual_start_date: null,
  manual_end_date: null,
};

function setupDefaultMocks() {
  vi.mocked(getProject).mockResolvedValue(baseProject);
  vi.mocked(fetchThumbnailUrl).mockResolvedValue(null);
  vi.mocked(getProjectDates).mockResolvedValue(baseDates);
  vi.mocked(getProjectFeedback).mockResolvedValue([]);
  vi.mocked(listProjects).mockResolvedValue([
    {
        project_summary_id: 42,
        project_name: "Test Project",
        project_key: null,
        project_type: null,
        project_mode: null,
        created_at: null,
        is_public: false
    },
  ]);
}

function renderPage() {
  return render(
    <MemoryRouter>
      <ProjectDetailPage />
    </MemoryRouter>
  );
}

describe("ProjectDetailPage", () => {
  beforeEach(() => {
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:mock-url"),
      revokeObjectURL: vi.fn(),
    });
    setupDefaultMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.unstubAllGlobals();
  });

  describe("loading and error states", () => {
    it("shows loading state initially", () => {
      vi.mocked(getProject).mockReturnValue(new Promise(() => {}) as never);
      renderPage();
      expect(screen.getByText("Loading…")).toBeInTheDocument();
    });

    it("shows error message when API fails", async () => {
      vi.mocked(getProject).mockRejectedValue(new Error("Not found"));
      renderPage();
      await waitFor(() => {
        expect(screen.getByText("Not found")).toBeInTheDocument();
      });
    });

    it("shows back button on error state", async () => {
      vi.mocked(getProject).mockRejectedValue(new Error("Failed"));
      renderPage();
      await waitFor(() => {
        expect(screen.getByText("← Back to Projects")).toBeInTheDocument();
      });
    });
  });

  describe("project content", () => {
    it("renders project name after loading", async () => {
      renderPage();
      await waitFor(() => {
        expect(screen.getAllByText("Test Project").length).toBeGreaterThan(0);
      });
    });

    it("renders project summary text", async () => {
      renderPage();
      await waitFor(() => {
        expect(screen.getByText("A test project summary.")).toBeInTheDocument();
      });
    });

    it("renders project type and mode metadata", async () => {
      renderPage();
      await waitFor(() => {
        expect(screen.getByText("personal")).toBeInTheDocument();
        expect(screen.getByText("solo")).toBeInTheDocument();
      });
    });

    it("renders date range", async () => {
      renderPage();
      await waitFor(() => {
        expect(screen.getByText(/2024-01-01/)).toBeInTheDocument();
        expect(screen.getByText(/2024-06-01/)).toBeInTheDocument();
      });
    });

    it("shows no-image placeholder when thumbnail is null", async () => {
      renderPage();
      await waitFor(() => {
        expect(screen.getByText("No Image")).toBeInTheDocument();
      });
    });

    it('shows "No feedback available" when feedback is empty', async () => {
      renderPage();
      await waitFor(() => {
        expect(
          screen.getByText("No feedback available for this project.")
        ).toBeInTheDocument();
      });
    });
  });

  describe("feedback display", () => {
    it("renders feedback grouped by skill", async () => {
      vi.mocked(getProjectFeedback).mockResolvedValue([
        {
          feedback_id: 1,
          skill_name: "code_quality",
          file_name: "main.ts",
          criterion_key: "ck1",
          criterion_label: "Quality",
          expected: null,
          suggestion: "Use more types.",
          generated_at: null,
        },
        {
          feedback_id: 2,
          skill_name: "code_quality",
          file_name: "utils.ts",
          criterion_key: "ck2",
          criterion_label: "Quality",
          expected: null,
          suggestion: "Avoid any.",
          generated_at: null,
        },
        {
          feedback_id: 3,
          skill_name: "testing",
          file_name: "app.test.ts",
          criterion_key: "ck3",
          criterion_label: "Testing",
          expected: null,
          suggestion: "Add edge cases.",
          generated_at: null,
        },
      ]);

      renderPage();

      await waitFor(() => {
        expect(screen.getByText("Code Quality")).toBeInTheDocument();
        expect(screen.getByText("Testing")).toBeInTheDocument();
        expect(screen.getByText("Use more types.")).toBeInTheDocument();
        expect(screen.getByText("Avoid any.")).toBeInTheDocument();
        expect(screen.getByText("Add edge cases.")).toBeInTheDocument();
      });
    });

    it("renders feedback file names", async () => {
      vi.mocked(getProjectFeedback).mockResolvedValue([
        {
          feedback_id: 1,
          skill_name: "testing",
          file_name: "app.test.ts",
          criterion_key: "ck1",
          criterion_label: "Testing",
          expected: null,
          suggestion: "Add more tests.",
          generated_at: null,
        },
      ]);

      renderPage();

      await waitFor(() => {
        expect(screen.getByText("app.test.ts")).toBeInTheDocument();
      });
    });
  });

  describe("delete project", () => {
    it("shows delete confirmation dialog after clicking Delete Project", async () => {
      const user = userEvent.setup();
      renderPage();

      await waitFor(() => screen.getByText("Delete Project"));
      await user.click(screen.getByText("Delete Project"));

      expect(
        screen.getByText("Are you sure? This cannot be undone.")
      ).toBeInTheDocument();
    });

    it("can cancel the delete confirmation", async () => {
      const user = userEvent.setup();
      renderPage();

      await waitFor(() => screen.getByText("Delete Project"));
      await user.click(screen.getByText("Delete Project"));
      await user.click(screen.getByText("Cancel"));

      expect(
        screen.queryByText("Are you sure? This cannot be undone.")
      ).not.toBeInTheDocument();
    });

    it("calls deleteProject and navigates to /projects on confirm", async () => {
      vi.mocked(deleteProject).mockResolvedValue(undefined);
      const user = userEvent.setup();
      renderPage();

      await waitFor(() => screen.getByText("Delete Project"));
      await user.click(screen.getByText("Delete Project"));
      await user.click(screen.getByText("Yes, delete"));

      await waitFor(() => {
        expect(deleteProject).toHaveBeenCalledWith(42);
        expect(mockNavigate).toHaveBeenCalledWith("/projects");
      });
    });

    it("shows error message when delete fails", async () => {
      vi.mocked(deleteProject).mockRejectedValue(new Error("Delete failed"));
      const user = userEvent.setup();
      renderPage();

      await waitFor(() => screen.getByText("Delete Project"));
      await user.click(screen.getByText("Delete Project"));
      await user.click(screen.getByText("Yes, delete"));

      await waitFor(() => {
        expect(screen.getByText("Delete failed")).toBeInTheDocument();
      });
    });
  });

  describe("dates editing", () => {
    it("shows date edit form after clicking Edit", async () => {
      const user = userEvent.setup();
      renderPage();

      await waitFor(() => screen.getByText("Edit"));
      await user.click(screen.getByText("Edit"));

      expect(screen.getByLabelText("Start date")).toBeInTheDocument();
      expect(screen.getByLabelText("End date")).toBeInTheDocument();
    });

    it("cancels date editing and restores original values", async () => {
      const user = userEvent.setup();
      renderPage();

      await waitFor(() => screen.getByText("Edit"));
      await user.click(screen.getByText("Edit"));
      await user.click(screen.getByText("Cancel"));

      expect(screen.queryByLabelText("Start date")).not.toBeInTheDocument();
    });

    it("calls patchProjectDates with correct args on save", async () => {
      vi.mocked(patchProjectDates).mockResolvedValue({
        ...baseDates,
        source: "MANUAL",
      });

      const user = userEvent.setup();
      renderPage();

      await waitFor(() => screen.getByText("Edit"));
      await user.click(screen.getByText("Edit"));
      await user.click(screen.getByText("Save"));

      await waitFor(() => {
        expect(patchProjectDates).toHaveBeenCalledWith(
          42,
          "2024-01-01",
          "2024-06-01"
        );
      });
    });

    it('shows "Reset to auto" button when dates source is MANUAL', async () => {
      vi.mocked(getProjectDates).mockResolvedValue({
        ...baseDates,
        source: "MANUAL",
      });

      const user = userEvent.setup();
      renderPage();

      await waitFor(() => screen.getByText("Edit"));
      await user.click(screen.getByText("Edit"));

      expect(screen.getByText("Reset to auto")).toBeInTheDocument();
    });

    it("calls resetProjectDates when Reset to auto is clicked", async () => {
      vi.mocked(getProjectDates).mockResolvedValue({
        ...baseDates,
        source: "MANUAL",
      });
      vi.mocked(resetProjectDates).mockResolvedValue({
        ...baseDates,
        source: "AUTO",
      });

      const user = userEvent.setup();
      renderPage();

      await waitFor(() => screen.getByText("Edit"));
      await user.click(screen.getByText("Edit"));
      await user.click(screen.getByText("Reset to auto"));

      await waitFor(() => {
        expect(resetProjectDates).toHaveBeenCalledWith(42);
      });
    });

    it('shows "manual" tag when dates source is MANUAL (view mode)', async () => {
      vi.mocked(getProjectDates).mockResolvedValue({
        ...baseDates,
        source: "MANUAL",
      });

      renderPage();

      await waitFor(() => {
        expect(screen.getByText("manual")).toBeInTheDocument();
      });
    });
  });

  describe("thumbnail", () => {
    it("shows Upload Thumbnail button when no thumbnail", async () => {
      renderPage();

      await waitFor(() => {
        expect(screen.getByText("Upload Thumbnail")).toBeInTheDocument();
      });
    });

    it("shows Change Thumbnail and Remove Thumbnail when thumbnail exists", async () => {
      vi.mocked(fetchThumbnailUrl).mockResolvedValue("blob:mock-url");

      renderPage();

      await waitFor(() => {
        expect(screen.getByText("Change Thumbnail")).toBeInTheDocument();
        expect(screen.getByText("Remove Thumbnail")).toBeInTheDocument();
      });
    });

    it("calls deleteThumbnail and clears thumb when Remove is clicked", async () => {
      vi.mocked(fetchThumbnailUrl).mockResolvedValue("blob:mock-url");
      vi.mocked(deleteThumbnail).mockResolvedValue(undefined);

      const user = userEvent.setup();
      renderPage();

      await waitFor(() => screen.getByText("Remove Thumbnail"));
      await user.click(screen.getByText("Remove Thumbnail"));
      await waitFor(() => screen.getByText("Yes, remove"));
      await user.click(screen.getByText("Yes, remove"));

      await waitFor(() => {
        expect(deleteThumbnail).toHaveBeenCalledWith(42);
        expect(screen.getByText("No Image")).toBeInTheDocument();
      });
    });
  });

  describe("prev/next navigation", () => {
    it("shows next project button when current is not last", async () => {
      vi.mocked(listProjects).mockResolvedValue([
        {
            project_summary_id: 42,
            project_name: "Test Project",
            project_key: null,
            project_type: null,
            project_mode: null,
            created_at: null,
            is_public: false
        },
        {
            project_summary_id: 43,
            project_name: "Next Project",
            project_key: null,
            project_type: null,
            project_mode: null,
            created_at: null,
            is_public: false
        },
      ]);

      renderPage();

      await waitFor(() => {
        expect(screen.getByText(/Next Project/)).toBeInTheDocument();
      });
    });

    it("shows prev project button when current is not first", async () => {
      vi.mocked(listProjects).mockResolvedValue([
        {
            project_summary_id: 41,
            project_name: "Prev Project",
            project_key: null,
            project_type: null,
            project_mode: null,
            created_at: null,
            is_public: false
        },
        {
            project_summary_id: 42,
            project_name: "Test Project",
            project_key: null,
            project_type: null,
            project_mode: null,
            created_at: null,
            is_public: false
        },
      ]);

      renderPage();

      await waitFor(() => {
        expect(screen.getByText(/Prev Project/)).toBeInTheDocument();
      });
    });

    it("navigates to next project when next button is clicked", async () => {
      vi.mocked(listProjects).mockResolvedValue([
        {
            project_summary_id: 42,
            project_name: "Test Project",
            project_key: null,
            project_type: null,
            project_mode: null,
            created_at: null,
            is_public: false
        },
        {
            project_summary_id: 43,
            project_name: "Next Project",
            project_key: null,
            project_type: null,
            project_mode: null,
            created_at: null,
            is_public: false
        },
      ]);

      const user = userEvent.setup();
      renderPage();

      await waitFor(() => screen.getByText(/Next Project/));
      await user.click(screen.getByText(/Next Project/));

      expect(mockNavigate).toHaveBeenCalledWith("/projects/43");
    });

    it("hides nav row when project is the only one", async () => {
      const { container } = renderPage();

      await waitFor(() => screen.getAllByText("Test Project").length > 0);
      expect(container.querySelector(".pdNavBtn")).toBeNull();
    });
  });

  describe("collaborative project", () => {
    it("shows contribution summary section for collaborative projects", async () => {
      vi.mocked(getProject).mockResolvedValue({
        ...baseProject,
        project_mode: "collaborative",
        contributions: { manual_contribution_summary: "I built the frontend." },
      });

      renderPage();

      await waitFor(() => {
        expect(screen.getByText("Contribution Summary")).toBeInTheDocument();
        expect(screen.getByText("I built the frontend.")).toBeInTheDocument();
      });
    });

    it("shows LLM contribution summary when manual summary is missing", async () => {
      vi.mocked(getProject).mockResolvedValue({
        ...baseProject,
        project_mode: "collaborative",
        contributions: { llm_contribution_summary: "I led architecture and API integration." },
      });

      renderPage();

      await waitFor(() => {
        expect(screen.getByText("Contribution Summary")).toBeInTheDocument();
        expect(screen.getByText("I led architecture and API integration.")).toBeInTheDocument();
      });
    });

    it("falls back to text collaboration contribution summary", async () => {
      vi.mocked(getProject).mockResolvedValue({
        ...baseProject,
        project_mode: "collaborative",
        contributions: {
          text_collab: { contribution_summary: "I authored the methods and results sections." },
        },
      });

      renderPage();

      await waitFor(() => {
        expect(screen.getByText("Contribution Summary")).toBeInTheDocument();
        expect(screen.getByText("I authored the methods and results sections.")).toBeInTheDocument();
      });
    });
  });
});
