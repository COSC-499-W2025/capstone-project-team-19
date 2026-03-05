import type { TimelineEventDTO } from "../../../../api/insights";

type UndatedSortField = "skill_name" | "project_name" | "level";
type SortDirection = "asc" | "desc";

export default function UndatedPanel({
    events,
    sortedEvents,
    undatedSortField,
    setUndatedSortField,
    undatedSortDir,
    setUndatedSortDir,
}: {
    events: TimelineEventDTO[];
    sortedEvents: TimelineEventDTO[];
    undatedSortField: UndatedSortField;
    setUndatedSortField: (f: UndatedSortField) => void;
    undatedSortDir: SortDirection;
    setUndatedSortDir: React.Dispatch<React.SetStateAction<SortDirection>>;
}) {
    return (
        <div className="skill-timeline-panel">
            {events.length > 0 ? (
                <>
                <div className="skill-timeline-sort">
                    <label>Sort by</label>
                    <select value={undatedSortField} onChange={(e) => setUndatedSortField(e.target.value as UndatedSortField)}>
                        <option value="skill_name">Skill name</option>
                        <option value="project_name">Project</option>
                        <option value="level">Level</option>
                    </select>

                    <button 
                        type="button" 
                        className="skill-timeline-sort-dir" 
                        onClick={() => setUndatedSortDir((d) => (d === "asc" ? "desc" : "asc"))} 
                        title={undatedSortDir === "asc" ? "A→Z (click for Z→A)" : "Z→A (click for A→Z)"}>
                        
                        {undatedSortDir === "asc" ? "A→Z" : "Z→A"}
                    </button>
                </div>

                <ul>
                    {sortedEvents.map((e, i) => (
                    <li key={`undated-${i}`}>
                        <strong>{e.skill_name}</strong> ({e.level}) – {e.project_name} (
                        {e.score.toFixed(2)})
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