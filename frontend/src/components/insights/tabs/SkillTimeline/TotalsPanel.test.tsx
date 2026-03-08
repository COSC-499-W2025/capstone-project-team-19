import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TotalsPanel from "./TotalsPanel";
import type { SkillTimelineDTO } from "../../../../api/insights";

const mockTimelineWithBoth: SkillTimelineDTO = {
	dated: [],
	undated: [],
	current_totals: {
		"testing and ci": {
			cumulative_score: 0.9,
			projects: ["My App"],
			skill_type: "code",
		},
		clarity: {
			cumulative_score: 0.7,
			projects: ["Essay"],
			skill_type: "text",
		},
	},
	summary: { total_skills: 2, total_projects: 2, date_range: {}, skill_names: [] },
};

const mockTimelineCodeOnly: SkillTimelineDTO = {
	dated: [],
	undated: [],
	current_totals: {
		"testing and ci": {
			cumulative_score: 0.9,
			projects: ["My App"],
			skill_type: "code",
		},
	},
	summary: { total_skills: 1, total_projects: 1, date_range: {}, skill_names: [] },
};

describe("TotalsPanel", () => {
	it("shows empty state when no totals", () => {
		const empty: SkillTimelineDTO = {
			dated: [],
			undated: [],
			current_totals: {},
			summary: { total_skills: 0, total_projects: 0, date_range: {}, skill_names: [] },
		};
		render(<TotalsPanel timeline={empty} />);
		expect(screen.getByText(/no totals/i)).toBeInTheDocument();
	});

	it("shows all skills by default with All toggle active", () => {
		render(<TotalsPanel timeline={mockTimelineWithBoth} />);
		expect(screen.getByRole("button", { name: /all/i })).toHaveClass("active");
		expect(screen.getAllByText(/testing and ci/i).length).toBeGreaterThan(0);
		expect(screen.getAllByText(/clarity/i).length).toBeGreaterThan(0);
	});

	it("filters to code skills when Code clicked", async () => {
		const user = userEvent.setup();
		render(<TotalsPanel timeline={mockTimelineWithBoth} />);
		await user.click(screen.getByRole("button", { name: /^code$/i }));
		expect(screen.getByRole("button", { name: /^code$/i })).toHaveClass("active");
		expect(screen.getAllByText(/testing and ci/i).length).toBeGreaterThan(0);
		expect(screen.queryByText(/^Clarity$/)).not.toBeInTheDocument();
	});

	it("filters to text skills when Text clicked", async () => {
		const user = userEvent.setup();
		render(<TotalsPanel timeline={mockTimelineWithBoth} />);
		await user.click(screen.getByRole("button", { name: /^text$/i }));
		expect(screen.getByRole("button", { name: /^text$/i })).toHaveClass("active");
		expect(screen.getAllByText(/clarity/i).length).toBeGreaterThan(0);
		expect(screen.queryAllByText(/testing and ci/i).length).toBe(0);
	});

	it("shows empty message but keeps toolbar when filtering to type with no skills", async () => {
		const user = userEvent.setup();
		render(<TotalsPanel timeline={mockTimelineCodeOnly} />);
		await user.click(screen.getByRole("button", { name: /^text$/i }));
		expect(screen.getByText(/no text skills available/i)).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /all/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /^code$/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /^text$/i })).toBeInTheDocument();
	});

	it("shows sort controls", () => {
		render(<TotalsPanel timeline={mockTimelineWithBoth} />);
		expect(screen.getByText(/sort by/i)).toBeInTheDocument();
	});
});
