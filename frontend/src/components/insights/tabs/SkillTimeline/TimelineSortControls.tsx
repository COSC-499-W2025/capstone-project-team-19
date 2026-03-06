import type { TimelineSortField, SortDirection } from "./timelineSortTypes";

export default function TimelineSortControls({
    sortField,
    setSortField,
    sortDir,
    setSortDir,
}: {
    sortField: TimelineSortField;
    setSortField: (f: TimelineSortField) => void;
    sortDir: SortDirection;
    setSortDir: React.Dispatch<React.SetStateAction<SortDirection>>;
}) {
    return (
        <div className="skill-timeline-sort">
            <label>Sort by</label>

            <select value={sortField} onChange={(e) => setSortField(e.target.value as TimelineSortField)}>
                <option value="skill_name">Skill name</option>
                <option value="project_name">Project</option>
                <option value="level">Level</option>
                <option value="score">Score</option>
            </select>

            <button
                type="button"
                className="skill-timeline-sort-dir"
                onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
                title={
                    sortField === "score"
                        ? sortDir === "asc"
                            ? "Low→High (click for High→Low)"
                            : "High→Low (click for Low→High)"
                        : sortDir === "asc"
                        ? "A→Z (click for Z→A)"
                        : "Z→A (click for A→Z)"
                }
            >
                {sortField === "score"
                    ? sortDir === "asc"
                        ? "Low→High"
                        : "High→Low"
                    : sortDir === "asc"
                    ? "A→Z"
                    : "Z→A"}
            </button>
        </div>
    );
}