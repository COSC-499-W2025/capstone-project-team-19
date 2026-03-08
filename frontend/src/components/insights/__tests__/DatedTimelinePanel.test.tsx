import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DatedTimelinePanel from "../tabs/SkillTimeline/DatedTimelinePanel";
import type { SkillTimelineDTO } from "../../../api/insights";

const mockTimelineWithDated: SkillTimelineDTO = {
	dated: [
		{
			date: "2024-06-15",
			events: [
				{
					skill_name: "testing and ci",
					level: "Advanced",
					score: 0.9,
					project_name: "My App",
					skill_type: "code",
				},
				{
					skill_name: "clarity",
					level: "Intermediate",
					score: 0.7,
					project_name: "Essay",
					skill_type: "text",
				},
			],
			cumulative_skills: {},
		},
	],
	undated: [],
	current_totals: {},
	summary: { total_skills: 2, total_projects: 2, date_range: {}, skill_names: [] },
};

const mockTimelineEmpty: SkillTimelineDTO = {
	dated: [],
	undated: [],
	current_totals: {},
	summary: { total_skills: 0, total_projects: 0, date_range: {}, skill_names: [] },
};

describe("DatedTimelinePanel", () => {
	it("shows empty state when no dated events", () => {
		render(<DatedTimelinePanel timeline={mockTimelineEmpty} />);
		expect(screen.getByText(/no dated events/i)).toBeInTheDocument();
	});

	it("shows dated events grouped by date", () => {
		render(<DatedTimelinePanel timeline={mockTimelineWithDated} />);
		expect(screen.getByText(/jun\.\s*\d+,?\s*2024/i)).toBeInTheDocument();
		expect(screen.getAllByText(/testing and ci/i).length).toBeGreaterThan(0);
		expect(screen.getAllByText(/clarity/i).length).toBeGreaterThan(0);
		expect(screen.getByText(/My App/)).toBeInTheDocument();
		expect(screen.getByText(/Essay/)).toBeInTheDocument();
	});

	it("shows sort controls when there are dated events", () => {
		render(<DatedTimelinePanel timeline={mockTimelineWithDated} />);
		expect(screen.getByText(/sort by/i)).toBeInTheDocument();
	});

	it("toggles sort direction when direction button clicked", async () => {
		const user = userEvent.setup();
		render(<DatedTimelinePanel timeline={mockTimelineWithDated} />);
		const dirButton = screen.getByRole("button", { name: /A→Z/i });
		expect(dirButton).toBeInTheDocument();
		await user.click(dirButton);
		expect(screen.getByRole("button", { name: /Z→A/i })).toBeInTheDocument();
	});
});
