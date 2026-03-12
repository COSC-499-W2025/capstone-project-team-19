import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import UndatedPanel from "../tabs/SkillTimeline/UndatedPanel";
import type { TimelineEventDTO } from "../../../api/insights";

const mockEvents: TimelineEventDTO[] = [
	{
		skill_name: "clarity",
		level: "Intermediate",
		score: 0.7,
		project_name: "Essay",
		skill_type: "text",
	},
	{
		skill_name: "data_structures",
		level: "Advanced",
		score: 0.85,
		project_name: "Algo Project",
		skill_type: "code",
	},
];

describe("UndatedPanel", () => {
	it("shows empty state when no events", () => {
		render(<UndatedPanel events={[]} />);
		expect(screen.getByText(/no undated events/i)).toBeInTheDocument();
	});

	it("shows undated events with skill name, level, project, and score", () => {
		render(<UndatedPanel events={mockEvents} />);
		expect(screen.getAllByText(/clarity/i).length).toBeGreaterThan(0);
		expect(screen.getAllByText(/data.structures/i).length).toBeGreaterThan(0);
		expect(screen.getByText(/Essay/)).toBeInTheDocument();
		expect(screen.getByText(/Algo Project/)).toBeInTheDocument();
	});

	it("shows search input when there are events", () => {
		render(<UndatedPanel events={mockEvents} />);
		expect(screen.getByPlaceholderText(/search skills/i)).toBeInTheDocument();
	});

	it("filters skills by search", async () => {
		const user = userEvent.setup();
		render(<UndatedPanel events={mockEvents} />);
		await user.type(screen.getByPlaceholderText(/search skills/i), "clarity");
		expect(screen.getByText(/clarity/i)).toBeInTheDocument();
		expect(screen.queryByText(/data.structures/i)).not.toBeInTheDocument();
	});
});
