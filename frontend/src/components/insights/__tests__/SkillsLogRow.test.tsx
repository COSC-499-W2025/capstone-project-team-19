import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import SkillsLogRow from "../tabs/Skills/SkillsLogRow";

describe("SkillsLogRow", () => {
	it("renders skill, project, level and score", () => {
		render(<SkillsLogRow skill_name="testing" project_name="My Proj" level="Advanced" score={0.85} />);
		expect(screen.getByText("Testing")).toBeInTheDocument();
		expect(screen.getByText(/My Proj · advanced · 0\.85/)).toBeInTheDocument();
	});

	it("renders date when provided", () => {
		render(<SkillsLogRow skill_name="ci" project_name="App" level="Intermediate" score={0.7} date="2024-06-15" />);
		expect(screen.getByText(/Jun 1[45], 2024/)).toBeInTheDocument();
	});
});
