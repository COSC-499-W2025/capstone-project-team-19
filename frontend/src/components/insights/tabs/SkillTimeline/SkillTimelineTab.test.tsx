import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SkillTimelineTab from "./SkillTimelineTab";
import * as insights from "../../../../api/insights";

vi.mock("../../../../api/insights");

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
		render(<SkillTimelineTab />);
		expect(screen.getByText(/loading skill timeline/i)).toBeInTheDocument();
	});

	it("shows timeline header after load", async () => {
		render(<SkillTimelineTab />);
		await waitFor(() => {
			expect(screen.getByText(/2 Skills/)).toBeInTheDocument();
		});
		expect(screen.getByText(/2 Projects/)).toBeInTheDocument();
	});

	it("shows error when fetch fails", async () => {
		vi.mocked(insights.getSkillTimeline).mockRejectedValue(new Error("API error"));
		render(<SkillTimelineTab />);
		await waitFor(() => {
			expect(screen.getByText("API error")).toBeInTheDocument();
		});
	});

	it("shows nav buttons for Timeline, Current Totals, Undated Skills", async () => {
		render(<SkillTimelineTab />);
		await waitFor(() => {
			expect(screen.getByText(/2 Skills/)).toBeInTheDocument();
		});
		expect(screen.getByRole("button", { name: /timeline/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /current totals/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /undated skills/i })).toBeInTheDocument();
	});

	it("shows Timeline section by default", async () => {
		render(<SkillTimelineTab />);
		await waitFor(() => {
			expect(screen.getByText(/2 Skills/)).toBeInTheDocument();
		});
		expect(screen.getByText(/Testing and Ci/i)).toBeInTheDocument();
		expect(screen.getByText(/My App/i)).toBeInTheDocument();
	});

	it("switches to Current Totals when clicked", async () => {
		const user = userEvent.setup();
		render(<SkillTimelineTab />);
		await waitFor(() => {
			expect(screen.getByText(/2 Skills/)).toBeInTheDocument();
		});
		await user.click(screen.getByRole("button", { name: /current totals/i }));
		expect(screen.getByRole("button", { name: /current totals/i })).toHaveClass("active");
		expect(screen.getAllByText(/Testing and Ci/i).length).toBeGreaterThan(0);
		expect(screen.getAllByText(/Clarity/i).length).toBeGreaterThan(0);
	});

	it("switches to Undated Skills when clicked", async () => {
		const user = userEvent.setup();
		render(<SkillTimelineTab />);
		await waitFor(() => {
			expect(screen.getByText(/2 Skills/)).toBeInTheDocument();
		});
		await user.click(screen.getByRole("button", { name: /undated skills/i }));
		expect(screen.getByRole("button", { name: /undated skills/i })).toHaveClass("active");
		expect(screen.getByText(/clarity/i)).toBeInTheDocument();
		expect(screen.getByText(/Essay/i)).toBeInTheDocument();
	});
});
