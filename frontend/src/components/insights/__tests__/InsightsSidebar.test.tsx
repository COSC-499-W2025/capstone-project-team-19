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
		expect(screen.getByRole("button", { name: /current totals/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /undated skills/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /chronological skills/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /activity heatmap/i })).toBeInTheDocument();
	});

	it("marks active view with active class", () => {
		render(<InsightsSidebar activeView="skill-timeline-timeline" onChange={() => {}} />);
		expect(screen.getByRole("button", { name: /^timeline$/i })).toHaveClass("active");
		expect(screen.getByRole("button", { name: /ranked projects/i })).not.toHaveClass("active");
	});

	it("calls onChange when nav item clicked", async () => {
		const onChange = vi.fn();
		const user = userEvent.setup();
		render(<InsightsSidebar activeView="ranked-projects" onChange={onChange} />);
		await user.click(screen.getByRole("button", { name: /^timeline$/i }));
		expect(onChange).toHaveBeenCalledWith("skill-timeline-timeline");
	});
});
