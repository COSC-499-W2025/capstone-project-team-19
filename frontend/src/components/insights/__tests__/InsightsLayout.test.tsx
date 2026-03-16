import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import InsightsLayout from "../InsightsLayout";
import * as insights from "../../../api/insights";

vi.mock("../../../api/insights");

const mockRankings = {
	success: true,
	data: {
		rankings: [
			{ rank: 1, project_summary_id: 101, project_name: "Project A", score: 0.8, manual_rank: null },
		],
	},
	error: null,
};

const mockTimeline = {
	success: true,
	data: {
		dated: [],
		undated: [],
		current_totals: {},
		summary: { total_skills: 0, total_projects: 0, date_range: {}, skill_names: [] },
	},
	error: null,
};

/** Sidebar marks active item with border-l-sky-600 (no "active" class). */
function expectNavActive(button: HTMLElement) {
	expect(button.className).toContain("border-l-sky-600");
}
function expectNavInactive(button: HTMLElement) {
	expect(button.className).toContain("border-l-transparent");
}

describe("InsightsLayout", () => {
	beforeEach(() => {
		vi.mocked(insights.getRanking).mockResolvedValue(mockRankings);
		vi.mocked(insights.getSkillTimeline).mockResolvedValue(mockTimeline);
	});

	it("renders Insights header and sidebar", async () => {
		render(<InsightsLayout />);
		await waitFor(() => {
			expect(screen.getByRole("heading", { name: /insights/i })).toBeInTheDocument();
		});
		expect(screen.getByRole("button", { name: /ranked projects/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /^timeline$/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /skills overview/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /skills log/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /activity heatmap/i })).toBeInTheDocument();
	});

	it("shows Ranked Projects tab by default", async () => {
		render(<InsightsLayout />);
		await waitFor(() => {
			expect(screen.getByText("Project A")).toBeInTheDocument();
		});
		expectNavActive(screen.getByRole("button", { name: /ranked projects/i }));
	});

	it("switches to Skill Timeline when clicked", async () => {
		const user = userEvent.setup();
		render(<InsightsLayout />);
		await waitFor(() => {
			expect(screen.getByText("Project A")).toBeInTheDocument();
		});
		await user.click(screen.getByRole("button", { name: /^timeline$/i }));
		expectNavActive(screen.getByRole("button", { name: /^timeline$/i }));
		expectNavInactive(screen.getByRole("button", { name: /ranked projects/i }));
	});

	it("switches to Skills Logs when clicked", async () => {
		const user = userEvent.setup();
		render(<InsightsLayout />);
		await waitFor(() => {
			expect(screen.getByText("Project A")).toBeInTheDocument();
		});
		await user.click(screen.getByRole("button", { name: /skills log/i }));
		expectNavActive(screen.getByRole("button", { name: /skills log/i }));
		expect(screen.getAllByText(/skills log/i).length).toBeGreaterThan(0);
	});

	it("switches to Activity Heatmap when clicked", async () => {
		const user = userEvent.setup();
		render(<InsightsLayout />);
		await waitFor(() => {
			expect(screen.getByText("Project A")).toBeInTheDocument();
		});
		await user.click(screen.getByRole("button", { name: /activity heatmap/i }));
		expectNavActive(screen.getByRole("button", { name: /activity heatmap/i }));
		expect(screen.getAllByText(/activity heatmap/i).length).toBeGreaterThan(0);
	});
});
