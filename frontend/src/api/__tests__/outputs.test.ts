import { api } from "../client";
import { editResume } from "../outputs";

vi.mock("../client", () => ({
  api: {
    postJson: vi.fn(),
  },
}));

afterEach(() => {
  vi.clearAllMocks();
});

describe("editResume", () => {
  it("sends POST to /resume/{id}/edit with payload", async () => {
    const mockResponse = { success: true, data: { id: 5, name: "Updated" }, error: null };
    vi.mocked(api.postJson).mockResolvedValue(mockResponse);

    const payload = {
      name: "New Name",
    };
    const result = await editResume(5, payload);

    expect(api.postJson).toHaveBeenCalledWith("/resume/5/edit", payload);
    expect(result).toEqual(mockResponse);
  });

  it("sends project edit fields with scope", async () => {
    vi.mocked(api.postJson).mockResolvedValue({ success: true, data: null, error: null });

    await editResume(3, {
      project_summary_id: 10,
      scope: "resume_only",
      display_name: "My Project",
      summary_text: "A summary",
      key_role: "Lead Dev",
      contribution_bullets: ["Did X", "Did Y"],
      contribution_edit_mode: "replace",
    });

    expect(api.postJson).toHaveBeenCalledWith("/resume/3/edit", {
      project_summary_id: 10,
      scope: "resume_only",
      display_name: "My Project",
      summary_text: "A summary",
      key_role: "Lead Dev",
      contribution_bullets: ["Did X", "Did Y"],
      contribution_edit_mode: "replace",
    });
  });

  it("sends global scope", async () => {
    vi.mocked(api.postJson).mockResolvedValue({ success: true, data: null, error: null });

    await editResume(1, {
      project_summary_id: 7,
      scope: "global",
      key_role: "Backend Developer",
    });

    expect(api.postJson).toHaveBeenCalledWith("/resume/1/edit", {
      project_summary_id: 7,
      scope: "global",
      key_role: "Backend Developer",
    });
  });

  it("propagates API errors", async () => {
    vi.mocked(api.postJson).mockRejectedValue(new Error("Not found"));

    await expect(editResume(99, { name: "X" })).rejects.toThrow("Not found");
  });
});
