import { describe, it, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SkillProgressChart from "../tabs/Skills/SkillProgressChart";
import type { SkillTimelineDTO } from "../../../api/insights";

const mockTimelineWithDatedSkill: SkillTimelineDTO = {
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
			],
			cumulative_skills: {
				"testing and ci": {
					cumulative_score: 0.9,
					projects: ["My App"],
				},
			},
		},
		{
			date: "2024-07-20",
			events: [
				{
					skill_name: "testing and ci",
					level: "Expert",
					score: 0.5,
					project_name: "Another Project",
					skill_type: "code",
				},
			],
			cumulative_skills: {
				"testing and ci": {
					cumulative_score: 0.95,
					projects: ["My App", "Another Project"],
				},
			},
		},
	],
	undated: [
		{
			skill_name: "clarity",
			level: "Intermediate",
			score: 0.7,
			project_name: "Essay",
			skill_type: "text",
		},
	],
	current_totals: {},
	summary: {
		total_skills: 2,
		total_projects: 3,
		date_range: { earliest: "2024-06-15", latest: "2024-07-20" },
		skill_names: ["clarity", "testing and ci"],
	},
};

const mockTimelineEmpty: SkillTimelineDTO = {
	dated: [],
	undated: [],
	current_totals: {},
	summary: { total_skills: 0, total_projects: 0, date_range: {}, skill_names: [] },
};

const mockTimelineNoSkills: SkillTimelineDTO = {
	dated: [
		{
			date: "2024-06-15",
			events: [],
			cumulative_skills: {},
		},
	],
	undated: [],
	current_totals: {},
	summary: { total_skills: 0, total_projects: 0, date_range: {}, skill_names: [] },
};

describe("SkillProgressChart", () => {
	it("renders null when no dated events", () => {
		const { container } = render(<SkillProgressChart timeline={mockTimelineEmpty} />);
		expect(container.firstChild).toBeNull();
	});

	it("renders null when no skills", () => {
		const { container } = render(<SkillProgressChart timeline={mockTimelineNoSkills} />);
		expect(container.firstChild).toBeNull();
	});

	it("renders chart section with dropdown when there are skills and dated events", () => {
		render(<SkillProgressChart timeline={mockTimelineWithDatedSkill} />);
		expect(screen.getByRole("heading", { name: /skill progress over time/i })).toBeInTheDocument();
		expect(screen.getByText(/view how a skill's cumulative score has improved/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/select skill/i)).toBeInTheDocument();
	});

	it("shows all skills in the dropdown", () => {
		render(<SkillProgressChart timeline={mockTimelineWithDatedSkill} />);
		const select = screen.getByLabelText(/select skill/i);
		expect(within(select).getByRole("option", { name: /clarity/i })).toBeInTheDocument();
		expect(within(select).getByRole("option", { name: /testing and ci/i })).toBeInTheDocument();
	});

	it("shows 'No dated progress' when selected skill has only undated events", () => {
		render(<SkillProgressChart timeline={mockTimelineWithDatedSkill} />);
		// clarity is first in skill_names, has no dated progress
		expect(screen.getByText(/no dated progress for this skill/i)).toBeInTheDocument();
	});

	it("shows line chart when selected skill has dated progress", async () => {
		render(<SkillProgressChart timeline={mockTimelineWithDatedSkill} />);
		const select = screen.getByLabelText(/select skill/i);
		await userEvent.selectOptions(select, "testing and ci");
		// Selecting a skill with dated progress hides "No dated progress" and shows the chart
		// (Recharts SVG may not render in JSDOM due to 0x0 ResponsiveContainer dimensions)
		expect(screen.queryByText(/no dated progress for this skill/i)).not.toBeInTheDocument();
	});

	it("updates chart when dropdown selection changes", async () => {
		render(<SkillProgressChart timeline={mockTimelineWithDatedSkill} />);
		expect(screen.getByText(/no dated progress for this skill/i)).toBeInTheDocument();

		const select = screen.getByLabelText(/select skill/i);
		await userEvent.selectOptions(select, "testing and ci");
		expect(screen.queryByText(/no dated progress for this skill/i)).not.toBeInTheDocument();

		await userEvent.selectOptions(select, "clarity");
		expect(screen.getByText(/no dated progress for this skill/i)).toBeInTheDocument();
	});
});
