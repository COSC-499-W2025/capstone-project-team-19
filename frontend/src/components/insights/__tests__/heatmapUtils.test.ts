import { describe, it, expect } from "vitest";
import { getColorForValue, HEATMAP_COLORS } from "../tabs/Projects/heatmapUtils";

describe("getColorForValue", () => {
	it("returns empty color for zero", () => {
		expect(getColorForValue(0, 10)).toBe(HEATMAP_COLORS[0]);
	});
	it("scales by max value", () => {
		expect(getColorForValue(5, 10)).toBe(HEATMAP_COLORS[2]); // 50%
		expect(getColorForValue(10, 10)).toBe(HEATMAP_COLORS[4]);
	});
});
