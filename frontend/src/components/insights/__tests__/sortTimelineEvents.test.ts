import { describe, it, expect } from "vitest";
import { sortTimelineEvents } from "../tabs/SkillTimeline/utils/sortTimelineEvents";
import type { TimelineEventDTO } from "../../../api/insights";

const makeEvent = (overrides: Partial<TimelineEventDTO>): TimelineEventDTO => ({
	skill_name: "skill",
	project_name: "Project",
	level: "Intermediate",
	score: 0.5,
	...overrides,
});

describe("sortTimelineEvents", () => {
	const events: TimelineEventDTO[] = [
		makeEvent({ skill_name: "clarity", project_name: "Essay", level: "Beginner", score: 0.3 }),
		makeEvent({ skill_name: "api design", project_name: "API App", level: "Advanced", score: 0.9 }),
		makeEvent({ skill_name: "testing", project_name: "Tests", level: "Intermediate", score: 0.6 }),
	];

	it("returns empty array for empty input", () => {
		expect(sortTimelineEvents([], "skill_name", "asc")).toEqual([]);
	});

	it("returns copy for single event", () => {
		const single = [makeEvent({ skill_name: "only" })];
		const result = sortTimelineEvents(single, "skill_name", "asc");
		expect(result).toHaveLength(1);
		expect(result[0].skill_name).toBe("only");
		expect(result).not.toBe(single);
	});

	it("sorts by skill_name ascending", () => {
		const result = sortTimelineEvents(events, "skill_name", "asc");
		expect(result.map((e) => e.skill_name)).toEqual(["api design", "clarity", "testing"]);
	});

	it("sorts by skill_name descending", () => {
		const result = sortTimelineEvents(events, "skill_name", "desc");
		expect(result.map((e) => e.skill_name)).toEqual(["testing", "clarity", "api design"]);
	});

	it("sorts by project_name ascending", () => {
		const result = sortTimelineEvents(events, "project_name", "asc");
		expect(result.map((e) => e.project_name)).toEqual(["API App", "Essay", "Tests"]);
	});

	it("sorts by project_name descending", () => {
		const result = sortTimelineEvents(events, "project_name", "desc");
		expect(result.map((e) => e.project_name)).toEqual(["Tests", "Essay", "API App"]);
	});

	it("sorts by level ascending", () => {
		const result = sortTimelineEvents(events, "level", "asc");
		expect(result.map((e) => e.level)).toEqual(["Advanced", "Beginner", "Intermediate"]);
	});

	it("sorts by level descending", () => {
		const result = sortTimelineEvents(events, "level", "desc");
		expect(result.map((e) => e.level)).toEqual(["Intermediate", "Beginner", "Advanced"]);
	});

	it("sorts by score ascending", () => {
		const result = sortTimelineEvents(events, "score", "asc");
		expect(result.map((e) => e.score)).toEqual([0.3, 0.6, 0.9]);
	});

	it("sorts by score descending", () => {
		const result = sortTimelineEvents(events, "score", "desc");
		expect(result.map((e) => e.score)).toEqual([0.9, 0.6, 0.3]);
	});

	it("does not mutate original array", () => {
		const copy = [...events];
		sortTimelineEvents(events, "skill_name", "asc");
		expect(events).toEqual(copy);
	});
});
