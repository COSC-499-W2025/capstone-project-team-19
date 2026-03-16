import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ActivityHeatmapTab from "../tabs/Projects/ActivityHeatmapTab";
import * as projects from "../../../api/projects";

vi.mock("../../../api/projects");

describe("ActivityHeatmapTab", () => {
	beforeEach(() => {
		vi.mocked(projects.listProjects).mockResolvedValue([
			{ project_summary_id: 1, project_name: "Proj A", project_key: null, project_type: null, project_mode: null, created_at: null },
		]);
		vi.mocked(projects.getActivityHeatmapData).mockResolvedValue({
			project_id: 1, project_name: "Proj A", matrix: [[1]], row_labels: ["S1"], col_labels: ["v1"], mode: "snapshot", normalize: false, include_unclassified_text: false, title: "",
		});
	});

	it("shows Choose a project when none selected", async () => {
		render(<ActivityHeatmapTab />);
		await waitFor(() => expect(screen.getByText(/choose a project/i)).toBeInTheDocument());
	});

	it("shows heatmap after selecting project", async () => {
		const user = userEvent.setup();
		render(<ActivityHeatmapTab />);
		await waitFor(() => expect(screen.getByRole("combobox")).toBeInTheDocument());
		await user.selectOptions(screen.getByRole("combobox"), "1");
		await waitFor(() => expect(screen.getByRole("grid")).toBeInTheDocument());
		expect(screen.getByRole("heading", { name: "Proj A" })).toBeInTheDocument();
	});

	it("Select a project option is disabled", async () => {
		render(<ActivityHeatmapTab />);
		await waitFor(() => expect(screen.getByRole("combobox")).toBeInTheDocument());
		const opt = screen.getByRole("option", { name: /select a project/i });
		expect(opt).toBeDisabled();
	});
});
