import { useState, useMemo } from "react";
import type { SkillTimelineDTO } from "../../../../api/insights";
import { formatSkillName } from "./utils/formatHelpers";
import TimelineSortControls from "./TimelineSortControls";
import type { TimelineSortField, SortDirection } from "./utils/timelineSortTypes";

type TotalsView = "all" | "code" | "text";

export default function TotalsPanel({ timeline }: { timeline: SkillTimelineDTO }) {
    const [sortField, setSortField] = useState<TimelineSortField>("score");
    const [sortDir, setSortDir] = useState<SortDirection>("desc");
    const [totalsView, setTotalsView] = useState<TotalsView>("all");

    const entries = Object.entries(timeline.current_totals);

    //default toggle is all skill types (code/text)
    const filteredEntries = useMemo(() => {
        if (totalsView === "all") return entries;
        return entries.filter(([, data]) => data.skill_type === totalsView);
    }, [entries, totalsView]);

    if (entries.length === 0) return (
        <div className="skill-timeline-panel">
            <p>No totals.</p>
        </div>
    );

    const maxScore = Math.max(...filteredEntries.map(([, d]) => d.cumulative_score), 1);
    const sorted = [...filteredEntries].sort((a, b) => {
        if (sortField === "score") {
            const cmp = a[1].cumulative_score - b[1].cumulative_score;
            return sortDir === "asc" ? cmp : -cmp;
        }
        const cmp = a[0].toLowerCase().localeCompare(b[0].toLowerCase());
        return sortDir === "asc" ? cmp : -cmp;
    });

    return (
        <div className="skill-totals">
            <div className="skill-totals-toolbar">
                <TimelineSortControls
                    sortField={sortField}
                    setSortField={setSortField}
                    sortDir={sortDir}
                    setSortDir={setSortDir}
                    fields={["skill_name", "score"]}
                />

                <div className="skill-totals-toggle">
                    <button type="button" className={totalsView === "all" ? "active" : ""} onClick={() => setTotalsView("all")}>All</button>
                    <button type="button" className={totalsView === "code" ? "active" : ""} onClick={() => setTotalsView("code")}>Code</button>
                    <button type="button" className={totalsView === "text" ? "active" : ""} onClick={() => setTotalsView("text")}>Text</button>
                </div>
            </div>

            {filteredEntries.length === 0 ? (
                <p className="skill-totals-empty">No {totalsView} skills available.</p>
            ) : sorted.map(([skillName, data]) => {
                const pct = (data.cumulative_score / maxScore) * 100;

                return (
                <div key={skillName} className="skill-totals-row">
                    <div className="skill-totals-skill">{formatSkillName(skillName)}</div>

                    <div className="skill-totals-bar">
                        <div className="skill-bar-hover">
                            <div className="skill-totals-track">
                                <div className="skill-totals-fill" style={{ width: `${pct}%` }} />
                            </div>

                            {data.projects?.length ? (
                            <div className="skill-tooltip">
                                <div className="skill-tooltip-title">{formatSkillName(skillName)}</div>
                                <ul className="skill-tooltip-list">
                                {data.projects.map((projectName, i) => (
                                    <li key={`${projectName}-${i}`} className="skill-tooltip-item">
                                        <span className="skill-tooltip-project">{projectName}</span>
                                    </li>
                                ))}
                                </ul>
                            </div>
                            ) : null}
                        </div>
                    </div>

                    <div className="skill-totals-score">
                                        {typeof data.cumulative_score === "number"
                                            ? data.cumulative_score.toFixed(2)
                                            : "—"}
                                    </div>
                </div>
                );
            })}
        </div>
    );
}