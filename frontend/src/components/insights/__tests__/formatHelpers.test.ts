import { describe, it, expect } from "vitest";
import { formatSkillName, toYMD } from "../tabs/SkillTimeline/utils/formatHelpers";

describe("formatSkillName", () => {
	it("capitalizes first letter of each word when space-separated", () => {
		expect(formatSkillName("testing and ci")).toBe("Testing and Ci");
	});

	it("keeps minor words lowercase when not first", () => {
		expect(formatSkillName("testing and ci")).toBe("Testing and Ci");
		expect(formatSkillName("the quick brown fox")).toBe("The Quick Brown Fox");
	});

	it("capitalizes single word", () => {
		expect(formatSkillName("clarity")).toBe("Clarity");
	});

	it("preserves all-caps acronyms (length > 1)", () => {
		expect(formatSkillName("API")).toBe("API");
		expect(formatSkillName("CI")).toBe("CI");
	});

	it("does not split on underscores (treats as single word)", () => {
		expect(formatSkillName("data_structures")).toBe("Data_structures");
	});

	it("handles empty string", () => {
		expect(formatSkillName("")).toBe("");
	});

	it("handles single character", () => {
		expect(formatSkillName("a")).toBe("A");
	});
});

describe("toYMD", () => {
	it("returns empty string for null or undefined", () => {
		expect(toYMD(null)).toBe("");
		expect(toYMD(undefined)).toBe("");
	});

	it("formats ISO date string with period after month", () => {
		// ISO date with time to avoid timezone flakiness
		const result = toYMD("2024-06-15T12:00:00");
		expect(result).toMatch(/^[A-Za-z]{3}\./);
		expect(result).toContain("15");
		expect(result).toContain("2024");
	});

	it("handles ISO string with space instead of T", () => {
		const result = toYMD("2024-06-15 12:00:00");
		expect(result).toMatch(/^[A-Za-z]{3}\./);
		expect(result).toContain("2024");
	});

	it("returns empty string for empty string input", () => {
		expect(toYMD("")).toBe("");
	});
});
