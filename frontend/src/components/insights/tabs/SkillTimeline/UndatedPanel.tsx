import {useState, useMemo} from "react";
import type { TimelineEventDTO } from "../../../../api/insights";
import { formatSkillName } from "./utils/formatHelpers";
import TimelineSortControls from "./TimelineSortControls";
import type { TimelineSortField, SortDirection } from "./utils/timelineSortTypes";
import { sortTimelineEvents } from "./utils/sortTimelineEvents";

export default function UndatedPanel({events}: {
    events: TimelineEventDTO[];
}) {
    const [sortField, setSortField] = useState<TimelineSortField>("skill_name");
    const [sortDir, setSortDir] = useState<SortDirection>("asc");
    const sortedEvents = useMemo(() => {
        return sortTimelineEvents(events, sortField, sortDir);
    }, [events, sortField, sortDir]);

    return (
        <div className="w-full py-3 bg-white">
            {events.length > 0 ? (
                <>
                    <TimelineSortControls
                        sortField={sortField}
                        setSortField={setSortField}
                        sortDir={sortDir}
                        setSortDir={setSortDir}
                    />

                    <ul className="list-none p-0 m-0 border-t border-[#e5e5e5]">
                        {sortedEvents.map((e, i) => (
                            <li key={`undated-${i}`} className="py-3 border-b border-[#e5e5e5] text-sm leading-snug">
                                <strong className="font-bold text-[#1a1a1a]">{formatSkillName(e.skill_name)} </strong>
                                <span className="font-normal text-[#555]">
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