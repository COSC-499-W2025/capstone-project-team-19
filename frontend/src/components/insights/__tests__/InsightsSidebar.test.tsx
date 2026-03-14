import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import InsightsSidebar from "../InsightsSidebar";

describe("InsightsSidebar", () => {
	it("renders all nav items", () => {
		const onChange = vi.fn();
		render(<InsightsSidebar activeView="ranked-projects" onChange={onChange} />);
		expect(screen.getByRole("button", { name: /ranked projects/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /^timeline$/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /skills overview/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /skills logs/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /activity heatmap/i })).toBeInTheDocument();
	});

	it("marks active view with sky border (not literal active class)", () => {
		render(<InsightsSidebar activeView="skill-timeline-timeline" onChange={() => {}} />);
		const timelineBtn = screen.getByRole("button", { name: /^timeline$/i });
		const rankedBtn = screen.getByRole("button", { name: /ranked projects/i });
		expect(timelineBtn.className).toContain("border-l-sky-600");
		expect(rankedBtn.className).toContain("border-l-transparent");
	});

	it("calls onChange when nav item clicked", async () => {
		const onChange = vi.fn();
		const user = userEvent.setup();
		render(<InsightsSidebar activeView="ranked-projects" onChange={onChange} />);
		await user.click(screen.getByRole("button", { name: /^timeline$/i }));
		expect(onChange).toHaveBeenCalledWith("skill-timeline-timeline");
	});
});
