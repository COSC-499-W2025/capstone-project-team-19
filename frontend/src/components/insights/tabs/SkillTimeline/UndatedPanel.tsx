import {useState, useMemo} from "react";
import type { TimelineEventDTO } from "../../../../api/insights";
import { formatSkillName } from "./formatHelpers";
import TimelineSortControls from "./TimelineSortControls";
import type {TimelineSortField, SortDirection} from "./timelineSortTypes";
import { sortTimelineEvents } from "./sortTimelineEvents";

export default function UndatedPanel({events}: {
    events: TimelineEventDTO[];
}) {
    const [sortField, setSortField] = useState<TimelineSortField>("skill_name");
    const [sortDir, setSortDir] = useState<SortDirection>("asc");
    const sortedEvents = useMemo(() => {
        return sortTimelineEvents(events, sortField, sortDir);
    }, [events, sortField, sortDir]);

    return (
        <div className="skill-timeline-panel">
            {events.length > 0 ? (
                <>
                <TimelineSortControls
                    sortField={sortField}
                    setSortField={setSortField}
                    sortDir={sortDir}
                    setSortDir={setSortDir}
                />

                <ul className="skill-undated-list">
                    {sortedEvents.map((e, i) => (
                    <li key={`undated-${i}`} className="skill-undated-item">
                        <strong className="skill-undated-skill">{formatSkillName(e.skill_name)} </strong>
                        <span className="skill-undated-meta">
                            ({e.level}) - {e.project_name} ({e.score.toFixed(2)})
                        </span>
                    </li>
                    ))}
                </ul>
                </>
            ) : (
                <p>No undated events.</p>
            )}
        </div>
    );
}