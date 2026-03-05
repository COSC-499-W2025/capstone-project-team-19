import type { SkillTimelineDTO } from "../../../../api/insights";
import { formatSkillName } from "./formatSkillName";

export default function DatedTimelinePanel({ timeline }: { timeline: SkillTimelineDTO }) {
    return (
        <div className="skill-timeline-panel">
            {timeline.dated.length > 0 ? (
                <div className="skill-dated-timeline">
                    {timeline.dated.map((group) => (
                        <section key={group.date} className="skill-timeline-date-group">
                            <h3 className="skill-dated-heading">{group.date}</h3>
                            <ul className="skill-dated-list">
                                {group.events.map((e, i) => (
                                    <li key={`${group.date}-${i}`} className="skill-dated-item">
                                        <strong className="skill-undated-skill">{formatSkillName(e.skill_name)}</strong>
                                        <span className="skill-undated-meta">
                                            ({e.level}) – {e.project_name} ({e.score.toFixed(2)})
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        </section>
                    ))}
                </div>
            ) : (
                <p>No dated events.</p>
            )}
        </div>
    );
}