import { useState } from "react";
import type { SkillTimelineDTO } from "../../../../api/insights";
import { formatSkillName, toShortDate } from "./utils/formatHelpers";
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
                    <TimelineSortControls sortField={sortField} setSortField={setSortField} sortDir={sortDir} setSortDir={setSortDir} fields={["skill_name", "project_name", "level"]} />

                    <div className="flex flex-col">
                        {timeline.dated.map((group, i) => {
                            const sortedEvents = sortTimelineEvents(group.events, sortField, sortDir);
                            return (
                                <div key={group.date} className="flex gap-4">
                                    {/* Spine: dot + connecting line */}
                                    <div className="flex flex-col items-center w-6 flex-shrink-0">
                                        <div className="w-3 h-3 rounded-full bg-slate-600 border-2 border-white shadow-sm" />
                                        {i < timeline.dated.length - 1 && (
                                            <div className="flex-1 min-h-[2rem] w-0.5 bg-slate-300 mt-1" />
                                        )}
                                    </div>

                                    {/* Content */}
                                    <div className="flex-1 min-w-0 pb-6">
                                        <span className="text-base font-bold text-slate-800 block mb-3">{toShortDate(group.date)}</span>
                                        <div className="grid grid-cols-[1fr_8rem_1fr] gap-4 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                                            <span>Skill</span>
                                            <span>Level</span>
                                            <span>Project</span>
                                        </div>
                                        <ul className="list-none p-0 m-0">
                                            {sortedEvents.map((e, j) => (
                                                <li key={`${group.date}-${j}`} className="grid grid-cols-[1fr_8rem_1fr] gap-4 py-2.5 border-b border-slate-200 text-sm items-center">
                                                    <span className="font-semibold text-slate-900">{formatSkillName(e.skill_name)}</span>
                                                    <span className="text-slate-600 capitalize">{e.level.toLowerCase()}</span>
                                                    <span className="text-slate-600 truncate">{e.project_name}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
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