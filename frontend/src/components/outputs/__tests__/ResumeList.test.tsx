import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ResumeList from "../ResumeList";

vi.mock("../../../api/outputs", () => ({
  listResumes: vi.fn(),
  deleteResume: vi.fn(),
  downloadResumeDocx: vi.fn(),
  downloadResumePdf: vi.fn(),
}));

vi.mock("../ExportDropdown", () => ({
  default: ({ onDocx, onPdf }: { onDocx: () => void; onPdf: () => void }) => (
    <div>
      <button onClick={onDocx}>Export DOCX</button>
      <button onClick={onPdf}>Export PDF</button>
    </div>
  ),
}));

import {
  listResumes,
  deleteResume,
  downloadResumeDocx,
  downloadResumePdf,
} from "../../../api/outputs";

const sampleResumes = [
  { id: 1, name: "Resume A", created_at: "2026-01-15T00:00:00" },
  { id: 2, name: "Resume B", created_at: "2026-02-20T00:00:00" },
];

function mockList(resumes = sampleResumes) {
  vi.mocked(listResumes).mockResolvedValue({
    success: true,
    data: { resumes },
    error: null,
  } as any);
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("ResumeList", () => {
  it("renders loading state initially", () => {
    vi.mocked(listResumes).mockReturnValue(new Promise(() => {}));
    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={vi.fn()} />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders resume list after loading", async () => {
    mockList();
    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Resume A")).toBeInTheDocument();
    });
    expect(screen.getByText("Resume B")).toBeInTheDocument();
  });

  it("shows empty state when no resumes exist", async () => {
    mockList([]);
    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("No resumes yet. Create one to get started.")).toBeInTheDocument();
    });
  });

  it("shows error when list fails to load", async () => {
    vi.mocked(listResumes).mockRejectedValue(new Error("Server error"));
    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeInTheDocument();
    });
  });

  it("formats dates correctly", async () => {
    mockList([{ id: 1, name: "R", created_at: "2026-03-15T00:00:00" }]);
    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("March 15, 2026")).toBeInTheDocument();
    });
  });

  it("calls onView when View button is clicked", async () => {
    mockList();
    const onView = vi.fn();
    const user = userEvent.setup();
    render(<ResumeList onView={onView} onEdit={vi.fn()} onCreateNew={vi.fn()} />);

    await waitFor(() => screen.getByText("Resume A"));
    const viewButtons = screen.getAllByText("View");
    await user.click(viewButtons[0]);

    expect(onView).toHaveBeenCalledWith(1);
  });

  it("calls onEdit when Edit button is clicked", async () => {
    mockList();
    const onEdit = vi.fn();
    const user = userEvent.setup();
    render(<ResumeList onView={vi.fn()} onEdit={onEdit} onCreateNew={vi.fn()} />);

    await waitFor(() => screen.getByText("Resume A"));
    const editButtons = screen.getAllByText("Edit");
    await user.click(editButtons[0]);

    expect(onEdit).toHaveBeenCalledWith(1);
  });

  it("calls onCreateNew when Create button is clicked", async () => {
    mockList();
    const onCreateNew = vi.fn();
    const user = userEvent.setup();
    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={onCreateNew} />);

    await waitFor(() => screen.getByText("Resume A"));
    await user.click(screen.getByText("Create New Resume"));

    expect(onCreateNew).toHaveBeenCalled();
  });

  it("deletes resume after confirmation and reloads list", async () => {
    mockList();
    vi.mocked(deleteResume).mockResolvedValue({ success: true, data: null, error: null } as any);
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();

    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={vi.fn()} />);
    await waitFor(() => screen.getByText("Resume A"));

    await user.click(screen.getAllByText("Delete")[0]);

    expect(confirmSpy).toHaveBeenCalledWith("Delete this resume?");
    await waitFor(() => {
      expect(deleteResume).toHaveBeenCalledWith(1);
    });
    // listResumes called once on mount, once on reload after delete
    expect(listResumes).toHaveBeenCalledTimes(2);

    confirmSpy.mockRestore();
  });

  it("does not delete when confirmation is cancelled", async () => {
    mockList();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);
    const user = userEvent.setup();

    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={vi.fn()} />);
    await waitFor(() => screen.getByText("Resume A"));

    await user.click(screen.getAllByText("Delete")[0]);

    expect(deleteResume).not.toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it("shows error when delete fails", async () => {
    mockList();
    vi.mocked(deleteResume).mockRejectedValue(new Error("Delete failed"));
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();

    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={vi.fn()} />);
    await waitFor(() => screen.getByText("Resume A"));

    await user.click(screen.getAllByText("Delete")[0]);

    await waitFor(() => {
      expect(screen.getByText("Delete failed")).toBeInTheDocument();
    });
    confirmSpy.mockRestore();
  });

  it("triggers DOCX export", async () => {
    mockList();
    vi.mocked(downloadResumeDocx).mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={vi.fn()} />);
    await waitFor(() => screen.getByText("Resume A"));

    await user.click(screen.getAllByText("Export DOCX")[0]);

    await waitFor(() => {
      expect(downloadResumeDocx).toHaveBeenCalledWith(1);
    });
  });

  it("triggers PDF export", async () => {
    mockList();
    vi.mocked(downloadResumePdf).mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={vi.fn()} />);
    await waitFor(() => screen.getByText("Resume A"));

    await user.click(screen.getAllByText("Export PDF")[0]);

    await waitFor(() => {
      expect(downloadResumePdf).toHaveBeenCalledWith(1);
    });
  });

  it("shows heading as Resume", async () => {
    mockList();
    render(<ResumeList onView={vi.fn()} onEdit={vi.fn()} onCreateNew={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Resume" })).toBeInTheDocument();
    });
  });
});
