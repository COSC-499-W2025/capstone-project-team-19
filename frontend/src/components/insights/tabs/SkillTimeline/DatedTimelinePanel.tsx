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
        <div className="skill-timeline-panel">
            {timeline.dated.length > 0 ? (
                <>
                    <TimelineSortControls
                        sortField={sortField}
                        setSortField={setSortField}
                        sortDir={sortDir}
                        setSortDir={setSortDir}
                    />

                    <div className="skill-dated-timeline">
                        {timeline.dated.map((group) => {
                            const sortedEvents = sortTimelineEvents(group.events, sortField, sortDir);
                            return (
                                <section key={group.date} className="skill-timeline-date-group">
                                    <h3 className="skill-dated-heading">{toYMD(group.date)}</h3>
                                    <ul className="skill-dated-list">
                                        {sortedEvents.map((e, i) => (
                                            <li key={`${group.date}-${i}`} className="skill-dated-item">
                                                <strong className="skill-undated-skill">{formatSkillName(e.skill_name)} </strong>
                                                <span className="skill-undated-meta">
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