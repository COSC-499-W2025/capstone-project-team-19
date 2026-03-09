import type { TimelineEventDTO } from "../../../../../api/insights";
import type { TimelineSortField, SortDirection } from "./timelineSortTypes";

export function sortTimelineEvents(events: TimelineEventDTO[], sortField: TimelineSortField, sortDir: SortDirection) {
    return [...events].sort((a, b) => {
        let cmp = 0;

        switch (sortField) {
            case "skill_name":
                cmp = a.skill_name.localeCompare(b.skill_name);
                break;
            case "project_name":
                cmp = a.project_name.localeCompare(b.project_name);
                break;
            case "level":
                cmp = a.level.localeCompare(b.level);
                break;
            case "score":
                cmp = a.score - b.score;
                break;
        }

        return sortDir === "asc" ? cmp : -cmp;
    });
}
