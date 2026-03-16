import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SkillsLog from "../tabs/Skills/SkillsLog";
import * as insights from "../../../api/insights";

vi.mock("../../../api/insights");

const mockTimeline = {
	success: true,
	data: {
		dated: [{ date: "2024-06-15", events: [{ skill_name: "testing", level: "Advanced", score: 0.9, project_name: "Proj A" }], cumulative_skills: {} }],
		undated: [{ skill_name: "clarity", level: "Intermediate", score: 0.7, project_name: "Proj B" }],
		current_totals: {},
		summary: { total_skills: 2, total_projects: 2, date_range: {}, skill_names: ["testing", "clarity"] },
	},
	error: null,
};

describe("SkillsLog", () => {
	beforeEach(() => {
		vi.mocked(insights.getSkillTimeline).mockResolvedValue(mockTimeline);
	});

	it("shows loading then dated and undated sections", async () => {
		render(<SkillsLog />);
		expect(screen.getByText(/loading skill timeline/i)).toBeInTheDocument();
		await waitFor(() => expect(screen.getByText("Dated Skill Events")).toBeInTheDocument());
		expect(screen.getByText("Undated Skill Events")).toBeInTheDocument();
		expect(screen.getByText("Testing")).toBeInTheDocument();
		expect(screen.getByText("Clarity")).toBeInTheDocument();
	});

	it("shows error when fetch fails", async () => {
		vi.mocked(insights.getSkillTimeline).mockRejectedValue(new Error("Network error"));
		render(<SkillsLog />);
		await waitFor(() => expect(screen.getByText("Network error")).toBeInTheDocument());
	});

	it("filters by search and project", async () => {
		const user = userEvent.setup();
		render(<SkillsLog />);
		await waitFor(() => expect(screen.getByText("Testing")).toBeInTheDocument());
		await user.type(screen.getByLabelText(/search skills/i), "testing");
		expect(screen.getByText("Testing")).toBeInTheDocument();
		expect(screen.queryByText("Clarity")).not.toBeInTheDocument();
	});

});
