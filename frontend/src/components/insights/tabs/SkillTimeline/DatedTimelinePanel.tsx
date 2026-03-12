import { useState } from "react";
import type { SkillTimelineDTO } from "../../../../api/insights";
import { formatSkillName, toYMD } from "./utils/formatHelpers";
import TimelineSortControls from "./TimelineSortControls";
import type { TimelineSortField, SortDirection } from "./utils/timelineSortTypes";
import { sortTimelineEvents } from "./utils/sortTimelineEvents";

export default function DatedTimelinePanel({ timeline }: { timeline: SkillTimelineDTO }) {
    const [sortField, setSortField] = useState<TimelineSortField>("skill_name");
    const [sortDir, setSortDir] = useState<SortDirection>("asc");

    return (
        <div className="w-full py-3 bg-white">
            {timeline.dated.length > 0 ? (
                <>
                    <TimelineSortControls
                        sortField={sortField}
                        setSortField={setSortField}
                        sortDir={sortDir}
                        setSortDir={setSortDir}
                    />

                    <div className="flex flex-col gap-5">
                        {timeline.dated.map((group) => {
                            const sortedEvents = sortTimelineEvents(group.events, sortField, sortDir);
                            return (
                                <section key={group.date} className="flex flex-col gap-0">
                                    <h3 className="text-base font-bold text-[#333] m-0 mb-2 pb-1 border-b-2 border-[#e5e5e5]">{toYMD(group.date)}</h3>
                                    <ul className="list-none p-0 m-0 border-t border-[#e5e5e5]">
                                        {sortedEvents.map((e, i) => (
                                            <li key={`${group.date}-${i}`} className="py-2.5 border-b border-[#e5e5e5] text-sm leading-snug">
                                                <strong className="font-bold text-[#1a1a1a]">{formatSkillName(e.skill_name)} </strong>
                                                <span className="font-normal text-[#555]">
                                                    ({e.level}) – {e.project_name} ({e.score.toFixed(2)})
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                </section>
                            );
                        })}
                    </div>
                </>
            ) : (
                <p>No dated events.</p>
            )}
        </div>
    );
}