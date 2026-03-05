import type { SkillTimelineDTO } from "../../../../api/insights";

export default function TotalsPanel({ timeline }: { timeline: SkillTimelineDTO }) {
    const entries = Object.entries(timeline.current_totals);

    if (entries.length === 0) return <p>No totals.</p>;
    const maxScore = Math.max(...entries.map(([, d]) => d.cumulative_score), 1);
    const sorted = [...entries].sort((a, b) => b[1].cumulative_score - a[1].cumulative_score);

    const skillCount = sorted.length;
    const projectCount = timeline.current_totals ?? timeline.current_totals ?? 0;


    return (
        <div className="skill-totals">
            {sorted.map(([skillName, data]) => {
                const pct = (data.cumulative_score / maxScore) * 100;

                return (
                <div key={skillName} className="skill-totals-row">
                    <div className="skill-totals-skill">{skillName}</div>

                    <div className="skill-totals-bar">
                    <div className="skill-totals-track">
                        <div className="skill-totals-fill" style={{ width: `${pct}%` }} />
                    </div>
                    </div>

                    <div className="skill-totals-score">{data.cumulative_score.toFixed(2)}</div>
                </div>
                );
            })}
        </div>
    );
}