import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TimelineSortControls from "../tabs/SkillTimeline/TimelineSortControls";

describe("TimelineSortControls", () => {
	it("renders Sort by label and select", () => {
		render(
			<TimelineSortControls
				sortField="skill_name"
				setSortField={() => {}}
				sortDir="asc"
				setSortDir={() => {}}
			/>
		);
		expect(screen.getByText(/sort by/i)).toBeInTheDocument();
		expect(screen.getByRole("combobox")).toBeInTheDocument();
	});

	it("shows all sort options when fields not specified", () => {
		render(
			<TimelineSortControls
				sortField="skill_name"
				setSortField={() => {}}
				sortDir="asc"
				setSortDir={() => {}}
			/>
		);
		expect(screen.getByRole("option", { name: /skill name/i })).toBeInTheDocument();
		expect(screen.getByRole("option", { name: /project/i })).toBeInTheDocument();
		expect(screen.getByRole("option", { name: /level/i })).toBeInTheDocument();
		expect(screen.getByRole("option", { name: /score/i })).toBeInTheDocument();
	});

	it("filters options when fields specified", () => {
		render(
			<TimelineSortControls
				sortField="score"
				setSortField={() => {}}
				sortDir="desc"
				setSortDir={() => {}}
				fields={["skill_name", "score"]}
			/>
		);
		expect(screen.getByRole("option", { name: /skill name/i })).toBeInTheDocument();
		expect(screen.getByRole("option", { name: /score/i })).toBeInTheDocument();
		expect(screen.queryByRole("option", { name: /project/i })).not.toBeInTheDocument();
	});

	it("shows A→Z when sortDir asc and skill_name", () => {
		render(
			<TimelineSortControls
				sortField="skill_name"
				setSortField={() => {}}
				sortDir="asc"
				setSortDir={() => {}}
			/>
		);
		expect(screen.getByRole("button", { name: /A→Z/i })).toBeInTheDocument();
	});

	it("shows Low→High when sortDir asc and score", () => {
		render(
			<TimelineSortControls
				sortField="score"
				setSortField={() => {}}
				sortDir="asc"
				setSortDir={() => {}}
			/>
		);
		expect(screen.getByRole("button", { name: /low→high/i })).toBeInTheDocument();
	});

	it("calls setSortField when select changes", async () => {
		const setSortField = vi.fn();
		const user = userEvent.setup();
		render(
			<TimelineSortControls
				sortField="skill_name"
				setSortField={setSortField}
				sortDir="asc"
				setSortDir={() => {}}
			/>
		);
		await user.selectOptions(screen.getByRole("combobox"), "score");
		expect(setSortField).toHaveBeenCalledWith("score");
	});

	it("calls setSortDir when direction button clicked", async () => {
		const setSortDir = vi.fn();
		const user = userEvent.setup();
		render(
			<TimelineSortControls
				sortField="skill_name"
				setSortField={() => {}}
				sortDir="asc"
				setSortDir={setSortDir}
			/>
		);
		await user.click(screen.getByRole("button", { name: /A→Z/i }));
		expect(setSortDir).toHaveBeenCalled();
	});
});
