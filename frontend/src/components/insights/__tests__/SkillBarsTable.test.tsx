import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import SkillBarsTable from "../tabs/Skills/SkillBarsTable";

describe("SkillBarsTable", () => {
	it("renders skills sorted by score descending", () => {
		const entries: [string, { cumulative_score: number; projects: { name: string; date?: string | null }[] }][] = [
			["python", { cumulative_score: 0.5, projects: [{ name: "A" }] }],
			["javascript", { cumulative_score: 0.9, projects: [{ name: "B" }] }],
		];
		render(<SkillBarsTable entries={entries} maxScore={1} />);
		expect(screen.getByText("Skill")).toBeInTheDocument();
		expect(screen.getByText("Score")).toBeInTheDocument();
		expect(screen.getAllByText("Javascript").length).toBeGreaterThan(0);
		expect(screen.getAllByText("Python").length).toBeGreaterThan(0);
		expect(screen.getByText("0.90")).toBeInTheDocument();
		expect(screen.getByText("0.50")).toBeInTheDocument();
	});
});
