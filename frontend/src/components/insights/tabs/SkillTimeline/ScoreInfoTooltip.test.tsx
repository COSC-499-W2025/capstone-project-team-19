import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ScoreInfoTooltip from "./ScoreInfoTooltip";

describe("ScoreInfoTooltip", () => {
	it("renders ? button with aria-label", () => {
		render(<ScoreInfoTooltip />);
		const button = screen.getByRole("button", { name: /how are skill scores calculated/i });
		expect(button).toBeInTheDocument();
	});

	it("opens modal when ? button clicked", async () => {
		const user = userEvent.setup();
		render(<ScoreInfoTooltip />);
		await user.click(screen.getByRole("button", { name: /how are skill scores calculated/i }));
		expect(screen.getByRole("dialog")).toBeInTheDocument();
		expect(screen.getByText(/how skill scores work/i)).toBeInTheDocument();
	});

	it("closes modal when close button clicked", async () => {
		const user = userEvent.setup();
		render(<ScoreInfoTooltip />);
		await user.click(screen.getByRole("button", { name: /how are skill scores calculated/i }));
		expect(screen.getByRole("dialog")).toBeInTheDocument();
		await user.click(screen.getByRole("button", { name: /close/i }));
		expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
	});

	it("closes modal when overlay clicked", async () => {
		const user = userEvent.setup();
		render(<ScoreInfoTooltip />);
		await user.click(screen.getByRole("button", { name: /how are skill scores calculated/i }));
		const overlay = screen.getByRole("dialog");
		expect(overlay).toBeInTheDocument();
		await user.click(overlay);
		expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
	});
});
