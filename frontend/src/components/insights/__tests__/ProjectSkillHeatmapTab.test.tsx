import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ProjectSkillHeatmapTab from "../tabs/Projects/ProjectSkillHeatmapTab";
import * as insights from "../../../api/insights";

vi.mock("../../../api/insights");

const mockData = {
	title: "Activity by Date",
	row_labels: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
	col_labels: ["2024-01-07"],
	matrix: [[1], [0], [0], [0], [0], [0], [0]], // 7 rows (days) x 1 col (week)
	available_years: [2024],
	projects_by_date: { "2024-01-07": ["Proj A"] },
};

describe("ProjectSkillHeatmapTab", () => {
	beforeEach(() => {
		vi.mocked(insights.getActivityByDate).mockResolvedValue(mockData);
	});

	it("renders heatmap with year selector", async () => {
		render(<ProjectSkillHeatmapTab />);
		await waitFor(() => expect(screen.getByText("Activity by Date")).toBeInTheDocument());
		expect(screen.getByRole("combobox", { name: /year/i })).toBeInTheDocument();
		expect(screen.getByText("All years")).toBeInTheDocument();
	});

	it("calls getActivityByDate with year when selected", async () => {
		const user = userEvent.setup();
		render(<ProjectSkillHeatmapTab />);
		await waitFor(() => expect(screen.getByText("Activity by Date")).toBeInTheDocument());
		await user.selectOptions(screen.getByRole("combobox"), "2024");
		expect(insights.getActivityByDate).toHaveBeenLastCalledWith(2024);
	});
});
