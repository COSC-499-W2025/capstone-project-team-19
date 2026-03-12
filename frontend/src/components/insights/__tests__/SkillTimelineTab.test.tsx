import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import SkillTimelineTab from "../tabs/SkillTimeline/SkillTimelineTab";
import * as insights from "../../../api/insights";

vi.mock("../../../api/insights");

const mockTimeline = {
	dated: [
		{
			date: "2024-06-15",
			events: [
				{
					skill_name: "testing and ci",
					level: "Advanced",
					score: 0.9,
					project_name: "My App",
					skill_type: "code" as const,
				},
			],
			cumulative_skills: {
				"testing and ci": {
					cumulative_score: 0.9,
					projects: ["My App"],
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
			skill_type: "text" as const,
		},
	],
	current_totals: {
		"testing and ci": {
			cumulative_score: 0.9,
			projects: ["My App"],
			skill_type: "code" as const,
		},
		clarity: {
			cumulative_score: 0.7,
			projects: ["Essay"],
			skill_type: "text" as const,
		},
	},
	summary: {
		total_skills: 2,
		total_projects: 2,
		date_range: { earliest: "2024-06-15", latest: "2024-06-15" },
		skill_names: ["clarity", "testing and ci"],
	},
};

describe("SkillTimelineTab", () => {
	beforeEach(() => {
		vi.mocked(insights.getSkillTimeline).mockResolvedValue({
			success: true,
			data: mockTimeline,
			error: null,
		});
	});

	it("shows loading state initially", () => {
		render(<SkillTimelineTab activeSection="timeline" />);
		expect(screen.getByText(/loading skill timeline/i)).toBeInTheDocument();
	});

	it("shows timeline header after load", async () => {
		render(<SkillTimelineTab activeSection="timeline" />);
		await waitFor(() => {
			expect(screen.getByText(/2 Skills/)).toBeInTheDocument();
		});
		expect(screen.getByText(/2 Projects/)).toBeInTheDocument();
	});

	it("shows error when fetch fails", async () => {
		vi.mocked(insights.getSkillTimeline).mockRejectedValue(new Error("API error"));
		render(<SkillTimelineTab activeSection="timeline" />);
		await waitFor(() => {
			expect(screen.getByText("API error")).toBeInTheDocument();
		});
	});

	it("shows Timeline section when activeSection is timeline", async () => {
		render(<SkillTimelineTab activeSection="timeline" />);
		await waitFor(() => {
			expect(screen.getByText(/2 Skills/)).toBeInTheDocument();
		});
		expect(screen.getByText(/Testing and Ci/i)).toBeInTheDocument();
		expect(screen.getByText(/My App/i)).toBeInTheDocument();
	});

	it("shows Current Totals when activeSection is totals", async () => {
		render(<SkillTimelineTab activeSection="totals" />);
		await waitFor(() => {
			expect(screen.getByText(/2 Skills/)).toBeInTheDocument();
		});
		expect(screen.getAllByText(/Testing and Ci/i).length).toBeGreaterThan(0);
		expect(screen.getAllByText(/Clarity/i).length).toBeGreaterThan(0);
	});

	it("shows Undated Skills when activeSection is undated", async () => {
		render(<SkillTimelineTab activeSection="undated" />);
		await waitFor(() => {
			expect(screen.getByText(/2 Skills/)).toBeInTheDocument();
		});
		expect(screen.getByText(/clarity/i)).toBeInTheDocument();
		expect(screen.getByText(/Essay/i)).toBeInTheDocument();
	});
});
