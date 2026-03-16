import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import SkillsTimeline from "../tabs/Skills/SkillsTimeline";
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

describe("SkillsTimeline", () => {
	it("shows empty state when no dated events", () => {
		render(<SkillsTimeline timeline={mockTimelineEmpty} />);
		expect(screen.getByText(/no dated events/i)).toBeInTheDocument();
	});

	it("shows dated events grouped by date", () => {
		render(<SkillsTimeline timeline={mockTimelineWithDated} />);
		// toShortDate uses en-US e.g. "Jun 15, 2024"
		expect(screen.getByText(/2024/)).toBeInTheDocument();
		expect(screen.getAllByText(/testing and ci/i).length).toBeGreaterThan(0);
		expect(screen.getAllByText(/clarity/i).length).toBeGreaterThan(0);
		expect(screen.getByText(/My App/)).toBeInTheDocument();
		expect(screen.getByText(/Essay/)).toBeInTheDocument();
	});

	it("shows column headers for skill rows", () => {
		render(<SkillsTimeline timeline={mockTimelineWithDated} />);
		expect(screen.getByText(/^Skill$/)).toBeInTheDocument();
		expect(screen.getByText(/^Level$/)).toBeInTheDocument();
		expect(screen.getByText(/^Project$/)).toBeInTheDocument();
	});
});
