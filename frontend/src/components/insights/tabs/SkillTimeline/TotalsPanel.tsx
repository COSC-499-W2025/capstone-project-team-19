import type { SkillTimelineDTO } from "../../../../api/insights";
import { formatSkillName } from "./formatSkillName";

export default function TotalsPanel({ timeline }: { timeline: SkillTimelineDTO }) {
    const entries = Object.entries(timeline.current_totals);

    if (entries.length === 0) return <p>No totals.</p>;
    const maxScore = Math.max(...entries.map(([, d]) => d.cumulative_score), 1);
    const sorted = [...entries].sort((a, b) => b[1].cumulative_score - a[1].cumulative_score);

    return (
        <div className="skill-totals">
            {sorted.map(([skillName, data]) => {
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