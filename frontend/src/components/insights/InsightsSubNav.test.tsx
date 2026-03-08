import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import InsightsSubNav from "./InsightsSubNav";

describe("InsightsSubNav", () => {
	it("renders all four tab buttons", () => {
		const onChange = vi.fn();
		render(<InsightsSubNav activeTab="ranked-projects" onChange={onChange} />);
		expect(screen.getByRole("button", { name: /ranked projects/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /skill timeline/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /chronological skills/i })).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /activity heatmap/i })).toBeInTheDocument();
	});

	it("marks active tab with active class", () => {
		render(<InsightsSubNav activeTab="skill-timeline" onChange={() => {}} />);
		expect(screen.getByRole("button", { name: /skill timeline/i })).toHaveClass("active");
		expect(screen.getByRole("button", { name: /ranked projects/i })).not.toHaveClass("active");
	});

	it("calls onChange when tab clicked", async () => {
		const onChange = vi.fn();
		const user = userEvent.setup();
		render(<InsightsSubNav activeTab="ranked-projects" onChange={onChange} />);
		await user.click(screen.getByRole("button", { name: /skill timeline/i }));
		expect(onChange).toHaveBeenCalledWith("skill-timeline");
	});
});
