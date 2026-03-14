import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import HeatmapLegend from "../tabs/Projects/HeatmapLegend";

describe("HeatmapLegend", () => {
	it("renders Less, More and color swatches", () => {
		const { container } = render(<HeatmapLegend />);
		expect(screen.getByText("Less")).toBeInTheDocument();
		expect(screen.getByText("More")).toBeInTheDocument();
		expect(container.querySelectorAll("[aria-hidden]")).toHaveLength(5);
	});
});
