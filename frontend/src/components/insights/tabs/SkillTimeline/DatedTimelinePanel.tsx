import type { SkillTimelineDTO } from "../../../../api/insights";
import { formatSkillName } from "./formatSkillName";

export default function DatedTimelineDTO({ timeline }: { timeline: SkillTimelineDTO }) {
    return (
        <div className="skill-timeline-panel">
            {timeline.dated.length > 0 ? (
                timeline.dated.map((group) => (
                <div key={group.date} className="skill-timeline-date-group">
                    <h4>{group.date}</h4>
                    <ul>
                    {group.events.map((e, i) => (
                        <li key={`${group.date}-${i}`}>
                            <strong>{formatSkillName(e.skill_name)}</strong> ({e.level}) – {e.project_name} (
                            {e.score.toFixed(2)})
                        </li>
                    ))}
                    </ul>
                </div>
                ))
            ) : (
                <p>No dated events.</p>
            )}
        </div>
    );
}