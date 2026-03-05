import type { SkillTimelineDTO } from "../../../../api/insights";

export default function TotalsPanel({ timeline }: { timeline: SkillTimelineDTO }) {
    const entries = Object.entries(timeline.current_totals);

    return (
        <div className="skill-timeline-panel">
        {entries.length > 0 ? (
            <div className="skill-timeline-totals-grid">
            {entries.map(([skillName, data]) => (
                <div key={skillName} className="skill-timeline-total-card">
                    <strong>{skillName}</strong>
                    <span>Score: {data.cumulative_score.toFixed(2)}</span>
                    <span>Projects: {data.projects.join(", ")}</span>
                </div>
            ))}
            </div>
        ) : (
            <p>No totals.</p>
        )}
        </div>
    );
}